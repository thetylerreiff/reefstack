#!/usr/bin/env python3
"""Read a finished task record and emit its exact snapshot and handoff link.

Read-only and explicitly invoked; small tasks without records never need this.
The receipt proves which bytes were read, not that the record is semantically true.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import quote

MAX_RECORD_BYTES = 65536
RECEIPT_PREFIX = "REEFSTACK_HANDOFF "


def read_record(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("task record must be a regular file")
    with path.open("rb") as stream:
        data = stream.read(MAX_RECORD_BYTES + 1)
    if len(data) > MAX_RECORD_BYTES:
        raise ValueError("task record exceeds 64 KiB; keep the record concise and link evidence")
    content = data.decode("utf-8")
    if not content.strip():
        raise ValueError("task record is empty")
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "markdown_link": "[Task record](<" + quote(str(path), safe="/:") + ">)",
            "content": content}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="existing canonical task record")
    parser.add_argument("--no-guard", action="store_true",
                        help="honor user output constraints without native final-link enforcement")
    args = parser.parse_args()
    try:
        receipt = read_record(args.record)
    except (OSError, ValueError) as error:
        print("Cannot prepare handoff: " + str(error), file=sys.stderr)
        return 1
    if args.no_guard:
        receipt["native_guard"] = False
    # One structured receipt, including the complete text, lets adapters compare
    # this readback to the final file without heuristic shell-command parsing.
    print(RECEIPT_PREFIX + json.dumps(receipt, ensure_ascii=False))
    # Keep the exact user-facing line at the end, outside JSON escapes and the
    # record body. Long temporary-workspace paths are easy to mistype otherwise.
    print("\nRecord: " + receipt["markdown_link"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
