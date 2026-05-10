"""Append missing keys from an example env file into a local env file."""

from __future__ import annotations

import sys
from pathlib import Path


def env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip())
    return keys


def append_missing(example: Path, target: Path) -> int:
    if not example.exists():
        print(f"skip: {example} does not exist")
        return 0
    if not target.exists():
        target.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"created: {target}")
        return 1

    existing = env_keys(target)
    missing_lines: list[str] = []
    for line in example.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key not in existing:
            missing_lines.append(line)
            existing.add(key)

    if not missing_lines:
        print(f"ok: {target} already has all keys from {example}")
        return 0

    with target.open("a", encoding="utf-8") as handle:
        handle.write("\n\n# Added by make config-upgrade\n")
        handle.write("\n".join(missing_lines))
        handle.write("\n")
    print(f"updated: appended {len(missing_lines)} keys to {target}")
    return len(missing_lines)


def main() -> int:
    pairs = sys.argv[1:]
    if len(pairs) % 2 != 0:
        print("usage: config_upgrade.py EXAMPLE TARGET [EXAMPLE TARGET ...]", file=sys.stderr)
        return 2
    changed = 0
    for index in range(0, len(pairs), 2):
        changed += append_missing(Path(pairs[index]), Path(pairs[index + 1]))
    return 0 if changed >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
