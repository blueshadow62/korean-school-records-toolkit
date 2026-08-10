"""Verify NCIC-sourced course files against their original HWPX documents.

HWPX is a zip of XML, so text comes out in document order without the column
interleaving that plagues PDF extraction. Each corpus table cell must appear as a
subsequence of the source text; comparison is punctuation-insensitive because
middle dots and spacing differ between renderers.

Documents are matched to courses by achievement-standard code overlap, not by
filename, because the uploaded files have masked names.
"""
from __future__ import annotations

import argparse
import collections
import re
import struct
import sys
import unicodedata
import zipfile
import zlib
from pathlib import Path

import olefile

CODE_RE = re.compile(r"\[\d{2}[^\]\s]{1,14}\d{2}-\d{2}\]")


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


def hwpx_text(path: Path) -> str:
    parts = []
    with zipfile.ZipFile(path) as z:
        names = sorted(
            (n for n in z.namelist() if re.search(r"section\d+\.xml$", n)),
            key=lambda n: int(re.search(r"section(\d+)", n).group(1)),
        )
        for n in names:
            xml = z.read(n).decode("utf-8", "replace")
            parts.append(re.sub(r"<[^>]+>", " ", xml))
    return unicodedata.normalize("NFC", " ".join(parts))


HWPTAG_PARA_TEXT = 67


def hwp_text(path: Path) -> str:
    """Text of a legacy binary .hwp (OLE compound file).

    Body sections are raw-deflate streams of tag/level/size records; only
    PARA_TEXT carries characters. Inline control codes are dropped by filtering
    below-space code points -- leftover binary from extended controls is harmless
    because verification only asks whether corpus text appears in this haystack.
    """
    parts = []
    with olefile.OleFileIO(str(path)) as ole:
        compressed = bool(ole.openstream("FileHeader").read(256)[36] & 1)
        names = sorted(
            ("/".join(e) for e in ole.listdir() if e[0] == "BodyText"),
            key=lambda n: int(re.search(r"(\d+)$", n).group(1)),
        )
        for name in names:
            data = ole.openstream(name).read()
            if compressed:
                data = zlib.decompress(data, -15)
            pos = 0
            while pos + 4 <= len(data):
                (head,) = struct.unpack_from("<I", data, pos)
                pos += 4
                tag, size = head & 0x3FF, (head >> 20) & 0xFFF
                if size == 0xFFF:
                    (size,) = struct.unpack_from("<I", data, pos)
                    pos += 4
                if tag == HWPTAG_PARA_TEXT:
                    chunk = data[pos:pos + size].decode("utf-16-le", "replace")
                    parts.append("".join(c if c >= " " else " " for c in chunk))
                pos += size
    return unicodedata.normalize("NFC", " ".join(parts))


def source_text(path: Path) -> str:
    return hwp_text(path) if path.suffix.lower() == ".hwp" else hwpx_text(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--list", type=Path, required=True, help="one corpus-relative path per line")
    ap.add_argument("--hwpx", type=Path, nargs="+", required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    docs = []
    for p in args.hwpx:
        raw = source_text(p)
        docs.append((p.name, set(CODE_RE.findall(raw)), canon(raw)))
        print(f"loaded\t{p.name}\tcodes={len(docs[-1][1])}", flush=True)

    out, stats = [], collections.Counter()
    for rel in args.list.read_text(encoding="utf-8").split():
        rel = rel.replace("\\", "/")
        text = (args.corpus / rel).read_text(encoding="utf-8")
        want = set(CODE_RE.findall(re.sub(r"<[^>]+>", "", text)))
        best = max(docs, key=lambda d: len(want & d[1]))
        if not want or not (want & best[1]):
            stats["no-source"] += 1
            out.append(f"no-source\t{rel}\t{len(want)}")
            continue
        cells = cells_of(text)
        missing = [c for c in cells if not is_subseq(canon(c), best[2])]
        # Bracket-insensitive: HWP splits a code's brackets into separate runs when it
        # opens a section, so CODE_RE misses them on the source side even though the
        # code text is present.
        lost = [c for c in want if canon(c) not in best[2]]
        if missing or lost:
            stats["mismatch"] += 1
            out.append(f"MISMATCH\t{rel}\t{best[0]}\t셀{len(missing)}/{len(cells)}\t코드{len(lost)}/{len(want)}\t{(missing[0][:70] if missing else sorted(lost)[:3])}")
        else:
            stats["ok"] += 1
            out.append(f"ok\t{rel}\t{best[0]}\t셀{len(cells)}\t코드{len(want)}")

    args.report.write_text("\n".join(out) + "\n", encoding="utf-8")
    for k, v in sorted(stats.items()):
        sys.stdout.write(f"{k}\t{v}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
