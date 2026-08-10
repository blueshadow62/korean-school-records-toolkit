"""Convert every non-Korean NKIS PDF with kordoc v4 into a clean MD corpus."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path


IMAGE_RE = re.compile(r"!\[[^]]*\]\([^)]*\)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    # Git Bash exports POSIX-style PATH entries that Windows Python can't resolve,
    # so auto-detection often fails and the caller must be able to point at npx.cmd.
    parser.add_argument("--npx", default=None)
    args = parser.parse_args()
    npx = args.npx or shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise SystemExit("npx not found; pass --npx <path to npx.cmd>")
    args.output.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(args.pdf_root.glob("*.pdf")):
        if pdf.name.startswith("1. 국어과"):
            continue
        output = args.output / f"{pdf.stem}.md"
        if output.exists():
            print(f"skip-existing\t{pdf.name}", flush=True)
            continue
        # kordoc crashes natively on some PDFs; one bad file must not abort the batch.
        result = subprocess.run([npx, "-y", "kordoc@^4", str(pdf), "-o", str(output), "--silent"])
        if result.returncode != 0 or not output.exists():
            output.unlink(missing_ok=True)
            print(f"FAILED\t{pdf.name}\texit={result.returncode}", flush=True)
            continue
        output.write_text(IMAGE_RE.sub("", output.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        print(f"converted\t{pdf.name}", flush=True)
    images = args.output / "images"
    if images.exists():
        shutil.rmtree(images)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
