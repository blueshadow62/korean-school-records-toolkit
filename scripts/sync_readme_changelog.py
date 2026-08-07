#!/usr/bin/env python3
"""Sync the README.md changelog banner from the latest CHANGELOG.md entry."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
README_PATH = ROOT / "README.md"
START = "<!-- CHANGELOG:START -->"
END = "<!-- CHANGELOG:END -->"
MARKER_PATTERN = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)


def latest_entry(changelog_text: str) -> str:
    for line in changelog_text.splitlines():
        if line.startswith("## "):
            return line[len("## "):].strip()
    raise SystemExit("No '## ' entry found in CHANGELOG.md")


def render_banner(entry: str) -> str:
    return (
        f"{START}\n"
        f"> **최근 업데이트: {entry}** — 자세한 변경 내역은 "
        f"[CHANGELOG.md](CHANGELOG.md)를 확인하세요.\n"
        f"{END}"
    )


def sync(changelog_path: Path = CHANGELOG_PATH, readme_path: Path = README_PATH) -> bool:
    entry = latest_entry(changelog_path.read_text(encoding="utf-8"))
    banner = render_banner(entry)
    readme_text = readme_path.read_text(encoding="utf-8")
    if not MARKER_PATTERN.search(readme_text):
        raise SystemExit(
            f"{readme_path} is missing the {START} / {END} marker pair"
        )
    updated_text = MARKER_PATTERN.sub(banner, readme_text, count=1)
    if updated_text == readme_text:
        return False
    readme_path.write_text(updated_text, encoding="utf-8")
    return True


def main() -> int:
    changed = sync()
    print("README.md updated" if changed else "README.md already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
