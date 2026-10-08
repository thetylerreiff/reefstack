#!/usr/bin/env python3
"""Build a reproducible standalone Reefstack plugin archive."""

import argparse
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile


ROOT = Path(__file__).resolve().parent.parent
INCLUDED_DIRECTORIES = (
    "assets",
    "evaluations",
    "harness",
    "hooks",
    "references",
    "refs",
    "scripts",
    "settings",
    "skills",
    "tests",
)
INCLUDED_FILES = {"plugin.json", "README.md", "LICENSE", "VERIFICATION.md", "settings.json"}
EXCLUDED_DIRECTORY_NAMES = {
    ".agents", ".git", ".github", ".venv", "__pycache__", "build", "cache",
    "caches", "dist", "node_modules", "target", "venv",
}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(ValueError):
    """Raised when the requested archive cannot be built safely."""


def _is_within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _included_root_entries(root):
    names = set(INCLUDED_FILES)
    names.update(INCLUDED_DIRECTORIES)
    try:
        children = list(root.iterdir())
    except OSError as error:
        raise PackageError("cannot read plugin source: " + str(error))
    for child in children:
        if child.is_file() and child.name.startswith("CONTRIBUTING") and child.suffix == ".md":
            names.add(child.name)
        if child.name.startswith("LICENSE.") and child.is_file():
            names.add(child.name)
    return sorted(name for name in names if (root / name).exists() or (root / name).is_symlink())


def _collect_entries(root):
    """Return sorted (relative archive path, source path, is_directory) entries."""
    root = Path(root).resolve(strict=True)
    entries = [("reefstack/", root, True)]

    def visit(path, relative, ancestors):
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise PackageError("broken package path: {} ({})".format(relative, error))
        if not _is_within(resolved, root):
            raise PackageError("package path escapes source: " + str(relative))
        try:
            mode = resolved.stat().st_mode
        except OSError as error:
            raise PackageError("cannot inspect package path {}: {}".format(relative, error))

        if stat.S_ISDIR(mode):
            if resolved in ancestors:
                raise PackageError("cyclic directory symlink in package: " + str(relative))
            entries.append((relative.as_posix().rstrip("/") + "/", path, True))
            next_ancestors = ancestors | {resolved}
            try:
                children = sorted(path.iterdir(), key=lambda child: child.name)
            except OSError as error:
                raise PackageError("cannot read package directory {}: {}".format(relative, error))
            for child in children:
                if child.name.startswith(".") or child.name in EXCLUDED_DIRECTORY_NAMES:
                    continue
                child_relative = relative / child.name
                visit(child, child_relative, next_ancestors)
        elif stat.S_ISREG(mode):
            entries.append((relative.as_posix(), path, False))
        else:
            raise PackageError("unsupported file type in package: " + str(relative))

    for name in _included_root_entries(root):
        visit(root / name, PurePosixPath("reefstack") / name, frozenset())

    # ZIP entries are emitted in lexical order, independent of filesystem order.
    return sorted(entries, key=lambda entry: entry[0])


def build_archive(output, source=ROOT):
    """Create output ZIP, refusing existing targets and unsafe source links."""
    source = Path(source).resolve(strict=True)
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise PackageError("refusing to overwrite existing output: " + str(output))
    if not output.parent.is_dir():
        raise PackageError("output directory does not exist: " + str(output.parent))
    if _is_within(output.resolve(strict=False), source):
        raise PackageError("output must be outside the plugin source directory")

    entries = _collect_entries(source)
    if not any(name == "reefstack/plugin.json" for name, _, is_dir in entries if not is_dir):
        raise PackageError("plugin.json is missing from the package")

    created = False
    try:
        with output.open("xb") as raw:
            created = True
            with zipfile.ZipFile(raw, mode="w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9) as archive:
                for name, path, is_dir in entries:
                    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
                    info.create_system = 3
                    info.external_attr = ((stat.S_IFDIR | 0o755) if is_dir else
                                          (stat.S_IFREG | 0o644)) << 16
                    info.compress_type = zipfile.ZIP_STORED if is_dir else zipfile.ZIP_DEFLATED
                    if is_dir:
                        info.external_attr |= 0x10
                        archive.writestr(info, b"")
                    else:
                        with path.open("rb") as stream:
                            archive.writestr(info, stream.read(), compress_type=zipfile.ZIP_DEFLATED,
                                             compresslevel=9)
    except Exception:
        if created:
            try:
                output.unlink()
            except OSError:
                pass
        raise
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="path for the new ZIP archive")
    args = parser.parse_args(argv)
    try:
        result = build_archive(args.output)
    except (OSError, PackageError, zipfile.BadZipFile) as error:
        print("package failed: " + str(error), file=sys.stderr)
        return 1
    print(str(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
