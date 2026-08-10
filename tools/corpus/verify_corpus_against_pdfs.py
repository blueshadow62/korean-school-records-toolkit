"""Verify every rebuilt course file against its source PDF, cell by cell.

Each table cell must appear as a subsequence of the source text (other columns can
interleave). Comparison is punctuation-insensitive because kordoc and pdfminer render
middle dots differently (･ vs ・ vs ·), which is a rendering difference, not content loss.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber


def canon(s: str) -> str:
    return re.sub(r"[^가-힣0-9A-Za-z]", "", unicodedata.normalize("NFKC", s))


def is_subseq(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(ch in it for ch in needle)


def cells_of(text: str) -> list[str]:
    out = []
    for raw in re.findall(r"<td[^>]*>(.*?)</td>", text, flags=re.S):
        cell = re.sub(r"<[^>]+>", " ", raw)
        if len(canon(cell)) >= 10:
            out.append(cell)
    return out


def page_texts(pdf_path: Path) -> list[str]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                pages.append(canon(page.extract_text() or ""))
            except Exception:
                pages.append("")  # some pages fail to decompress; treated as no coverage
            page.flush_cache()
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--pdf-root", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--map", type=Path, required=True, help="slice report TSV: ok<TAB>rel<TAB>pdf-stem")
    args = ap.parse_args()

    by_pdf: dict[str, list[str]] = collections.defaultdict(list)
    for row in args.map.read_text(encoding="utf-8").splitlines():
        parts = row.split("\t")
        if len(parts) >= 3 and parts[0] == "ok":
            by_pdf[parts[2]].append(parts[1])

    stems = {p.stem[:28]: p for p in args.pdf_root.glob("*.pdf")}
    out, stats = [], collections.Counter()
    for stem, rels in sorted(by_pdf.items()):
        pdf_path = stems.get(stem)
        if pdf_path is None:
            for rel in rels:
                stats["no-pdf"] += 1
                out.append(f"no-pdf\t{rel}\t{stem}")
            continue
        pages = page_texts(pdf_path)
        spans = pages + [pages[i] + pages[i + 1] for i in range(len(pages) - 1)]
        for rel in rels:
            cells = cells_of((args.corpus / rel).read_text(encoding="utf-8"))
            missing = [c for c in cells if not any(is_subseq(canon(c), s) for s in spans)]
            if missing:
                stats["mismatch"] += 1
                out.append(f"MISMATCH\t{rel}\t{len(missing)}/{len(cells)}\t{missing[0][:70]}")
            else:
                stats["ok"] += 1
                out.append(f"ok\t{rel}\t{len(cells)}")
        print(f"{stem[:34]:36s} done", flush=True)

    args.report.write_text("\n".join(out) + "\n", encoding="utf-8")
    for k, v in sorted(stats.items()):
        sys.stdout.write(f"{k}\t{v}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
