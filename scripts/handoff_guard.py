#!/usr/bin/env python3
"""Read-only native Stop guard for an observed task_handoff.py invocation.

Only the current turn's native command events are supported. Alternate record
locations outside cwd/.reefstack/tasks are deliberately not opened. A missing
transcript or helper is uncovered, not evidence that a handoff was validated.
The helper's --no-guard flag preserves explicit user requests for no link. An
opt-out skips enforcement; it does not establish a verified handoff.
"""

import json
import os
from pathlib import Path
import re
import shlex
import sys
from urllib.parse import quote

# Hook execution must not create bytecode sidecars in the plugin installation.
sys.dont_write_bytecode = True
import context
import task_handoff

MAX_INPUT_BYTES = 65536
MAX_TRANSCRIPT_BYTES = 4 * 1024 * 1024
ROOT = Path(__file__).resolve().parent.parent


def helper_argument(command):
    """Return (observed, record argument, opt-out) for native argv/shell calls."""
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) for part in command
    ):
        return False, None, False
    token_lines = [command]
    if Path(command[0]).name in {"sh", "bash", "zsh", "dash"}:
        if len(command) != 3 or command[1] not in {"-c", "-lc", "-ic"}:
            return False, None, False
        token_lines = []
        heredocs = []
        for line in command[2].split("\n"):
            if heredocs:
                delimiter, strip_tabs = heredocs[0]
                if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                    heredocs.pop(0)
                continue
            try:
                lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
                lexer.whitespace_split = True
                tokens = list(lexer)
                token_lines.append(tokens)
                for index, token in enumerate(tokens[:-1]):
                    if token == "<<":
                        delimiter = tokens[index + 1]
                        strip_tabs = delimiter.startswith("-")
                        heredocs.append((delimiter[1:] if strip_tabs else delimiter, strip_tabs))
            except ValueError:
                continue
    segments = []
    for tokens in token_lines:
        segments.append([])
        for token in tokens:
            if token and all(char in ";&|()<>" for char in token):
                segments.append([])
            else:
                segments[-1].append(token)
    result = (False, None, False)
    for parts in segments:
        if not parts:
            continue
        if re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", Path(parts[0]).name):
            parts = parts[1:]
            while parts and parts[0] in {"-B", "-I", "-u", "-E", "-s"}:
                parts = parts[1:]
        if parts and Path(parts[0]).name == "task_handoff.py":
            args = [arg for arg in parts[1:] if arg != "--no-guard"]
            if args[:1] == ["--"]:
                args = args[1:]
            result = True, args[0] if len(args) == 1 else None, "--no-guard" in parts[1:]
    return result


def transcript_events(path):
    """Read a bounded tail, discarding an incomplete first JSON line."""
    with Path(path).open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        start = max(0, size - MAX_TRANSCRIPT_BYTES)
        stream.seek(start)
        raw = stream.read(MAX_TRANSCRIPT_BYTES)
    if start:
        raw = raw.partition(b"\n")[2]
    lines = raw.splitlines(keepends=True)
    for line in lines:
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if isinstance(event, dict):
            yield event


def safe_record_path(value, cwd):
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = cwd / path
    path = path.resolve()
    directory = cwd / ".reefstack" / "tasks"
    # Resolve the candidate but not the allowlist: a symlinked tasks directory
    # must not turn this into permission to read outside the workspace.
    try:
        path.relative_to(directory)
    except ValueError:
        return None
    return path if path != directory else None


def correction(payload, problem, current=None, path=None):
    line = "\nRecord: " + current["markdown_link"] if current else ""
    if payload.get("stop_hook_active") is True:
        return {"systemMessage": "Reefstack handoff remains unverified: " + problem + line}
    command = shlex.quote(str(ROOT / "scripts" / "task_handoff.py"))
    if path is not None:
        command += " " + shlex.quote(str(path))
    else:
        command += " <the existing task record under cwd/.reefstack/tasks>"
    return {"decision": "block", "reason": (
        "Reefstack handoff check: " + problem + " Re-run python3 " + command
        + " and copy its exact Record line into the final response."
        + " This continuation authorizes only reading the existing task record "
        "and correcting the final response. Preserve the user's scope; do not "
        "edit product files, the record, or configuration." + line
    )}


def guard_result(payload, root=ROOT, data_directory=None):
    if not isinstance(payload, dict):
        raise ValueError("hook input must be an object")
    if not context.load_settings(root, data_directory).get("enabled", True):
        return {}
    if payload.get("hook_event_name", "Stop") != "Stop":
        raise ValueError("hook event does not match Stop")
    identity = (payload.get("session_id"), payload.get("turn_id"))
    if not all(isinstance(value, str) and value for value in identity):
        return {}
    transcript = payload.get("transcript_path")
    cwd_value = payload.get("cwd")
    if not isinstance(transcript, str) or not isinstance(cwd_value, str) or not cwd_value:
        return {}
    latest = None
    try:
        for event in transcript_events(transcript):
            data = event.get("payload")
            if event.get("type") != "event_msg" or not isinstance(data, dict):
                continue
            if data.get("type") != "item_completed" or (
                data.get("thread_id"), data.get("turn_id")
            ) != identity:
                continue
            item = data.get("item")
            if not isinstance(item, dict) or item.get("type") != "CommandExecution":
                continue
            observed, argument, opted_out = helper_argument(item.get("command"))
            if observed:
                latest = item, argument, opted_out
    except OSError:
        return {}
    if latest is None:
        return {}
    item, argument, opted_out = latest
    if opted_out:
        return {}
    cwd = Path(cwd_value).resolve()
    path = safe_record_path(argument, cwd)
    if path is None:
        # Existing canonical records elsewhere are allowed by the workflow but
        # outside this guard's read boundary. Do not demand a replacement.
        return {}
    output = item.get("aggregated_output", item.get("stdout"))
    receipts = []
    if isinstance(output, str):
        for line in output.split("\n"):
            if line.startswith(task_handoff.RECEIPT_PREFIX):
                try:
                    receipts.append(json.loads(line[len(task_handoff.RECEIPT_PREFIX):]))
                except ValueError:
                    receipts.append(None)
    receipt = receipts[0] if len(receipts) == 1 else None
    succeeded = item.get("status") == "completed" and type(item.get("exit_code")) is int and item["exit_code"] == 0
    # A valid receipt opt-out expresses intent. It is independent of later
    # record changes and therefore never reads the file or claims validation.
    if succeeded and isinstance(receipt, dict) and set(receipt) == {
        "path", "sha256", "markdown_link", "content", "native_guard"
    } and receipt["native_guard"] is False and all(
        isinstance(receipt[key], str) for key in ("path", "sha256", "markdown_link", "content")
    ) and receipt["path"] == str(path) and re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"]) and (
        receipt["markdown_link"] == "[Task record](<" + quote(str(path), safe="/:") + ">)"
    ):
        return {}
    current = None
    try:
        current = task_handoff.read_record(path)
    except (OSError, ValueError, UnicodeError):
        return correction(payload, "The existing task record could not be read.", path=path)
    if not succeeded:
        return correction(payload, "The latest helper call did not succeed.", current, path)
    if receipt != current:
        return correction(payload, "The latest helper readback is missing, invalid, "
                          "or stale relative to the task record.", current, path)
    final = payload.get("last_assistant_message")
    if not isinstance(final, str) or current["markdown_link"] not in final:
        return correction(payload, "The final response is missing the exact task "
                          "record link from the helper.", current, path)
    return {}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("hook input exceeds 64 KiB")
        payload = json.loads(raw) if raw.strip() else {}
        result = guard_result(payload, data_directory=os.environ.get("PLUGIN_DATA"))
    except (OSError, ValueError, KeyError, UnicodeError) as error:
        reason = "a required local file could not be read" if isinstance(error, OSError) else str(error)
        result = {"systemMessage": "Reefstack handoff check unavailable: " + reason}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
