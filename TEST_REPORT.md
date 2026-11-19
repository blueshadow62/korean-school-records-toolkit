# Test report

## Unreleased — tested on 2026-11-19 (Windows, Python 3.14, Node.js 26, without `PYTHONUTF8`)

- Package contract tests (`tests/`, incl. dev/package drift check, the self-hosted marketplace file with both editions, the MIT notice of `korean-character-count`, `SECURITY.md`, the AI-use notice, and 31 tests of the documents-only edition, including the shared icon): 50 passed. In a fresh clone without the development source beside it: 50 run, 48 passed, 2 skipped (the dev/package checks).
- `write-school-records` package-local scripts: 205 run, 187 passed, 18 skipped (all 18 compare with a registered guideline original, which the package does not contain).
- `write-school-records` development source (originals registered): 228 run, 226 passed, 2 skipped.
- `korean-character-count` node tests: 3 passed.
- `verify_package.py`: passed. It now also checks that the documents-only edition equals a fresh build and follows the directory file rules.
- `python scripts/build_directory_edition.py --check`: passed. The documents-only edition has 321 files (314 `.md`, 4 `.json`, 2 `LICENSE`, 1 `.png`), 8,222,284 bytes in total; the largest file is 189,790 bytes.
- `claude plugin validate --strict .` (Claude Code 2.1.328): passed. No plugin-directory warning. The validator finds the icon at `.claude-plugin/icon.png`, so `plugin.json` has no `icon` entry.
- `claude plugin validate --strict editions/korean-school-records-lite`: passed. No plugin-directory warning.
- Icon: both editions carry the same `.claude-plugin/icon.png` (1024×1024 PNG, 12,438 bytes). The file in the full plugin is the original. The build copies it unchanged. `claude plugin validate` only checks that an icon exists. Real PNGs of 256×256, 1024×512, and 4096×4096 passed it. The icon check in `build_directory_edition.py` rejects them. It also checks that the file is a PNG with a good IHDR header, square, 512 to 2048 px on a side, under 2 MiB, and the same file in both editions. A fresh clone with `core.autocrlf=true` keeps both icons byte for byte.
- Local marketplace install with a separate `CLAUDE_CONFIG_DIR`: the full plugin lists 2 skills although its installed copy also holds `editions/`; the documents-only edition lists 1 skill.
- Behavior evaluation of the documents-only edition (`tests/eval-cases` cases A-01, B-01, D-01, FORBID-02, BATCH-01, ANALYZE-01, LEVEL-04, MEMO-01, and A-01 again without a code execution tool; one fresh agent per case, a separate agent for the second pass): first-pass string checks 9 of 9 passed; second-pass checks 31 passed, 0 partial, 0 failed; no safety errors; no response named a script or a command. Every character and byte value written in a draft's length section matched `analyze_record.py`. The run without code execution wrote `글자 수는 기계로 점검하지 못했습니다.` and gave no estimated value.
- Line endings: a checkout without `.gitattributes` and with `core.autocrlf=true` (371 of 372 files CRLF) passed the same package tests, node tests, `verify_package.py`, and `claude plugin validate --strict`.

## 3.0.0 — tested on 2026-11-19 (Windows, Python 3.14, Node.js 26, without `PYTHONUTF8`)

- The package no longer ships the guideline originals. `write-school-records` uses the guideline summaries.
- Package contract tests (`tests/`, incl. dev/package drift check and the "no guideline originals" check): 14 passed.
- `write-school-records` package-local scripts: 205 run, 187 passed, 18 skipped. All 18 skipped tests compare the summaries or the limit table with a registered guideline original, which the package does not contain.
- `write-school-records` development source (originals registered): 228 run, 226 passed, 2 skipped (JS cross-check skipped where the sibling skill is absent).
- `korean-character-count` node tests: 3 passed.
- `verify_package.py`: passed.

## 2.2.0 — tested on 2026-11-18 (Windows, Python 3.14, Node.js 26, without `PYTHONUTF8`)

- Package contract tests (`tests/`, incl. dev/package drift check): 12 passed.
- `write-school-records` package-local scripts: 152 passed.
- `write-school-records` development source: 170 passed, 2 skipped (JS cross-check skipped where the sibling skill is absent).
- `korean-character-count` node tests: 3 passed.
- `verify_package.py`: passed.
- The tests now pass in the default Windows console (cp949) without `PYTHONUTF8=1`.
- Behavior eval cases (`tests/eval-cases/`): schema tests passed; model-run scoring not yet performed.

## 2.1.0 — tested on 2026-08-30 (Windows, Python 3.14, Node.js 24)

- Package contract tests (`tests/`, incl. dev/package drift check): 11 passed.
- `write-school-records` package-local scripts: 116 passed.
- `write-school-records` development source: 123 passed, 2 skipped (JS cross-check skipped where the sibling skill is absent).
- `korean-character-count` node tests: 3 passed.
- `verify_package.py`: passed.
- NEIS byte contract: both skills now agree on all 15 synthetic cases (line break = 1 Byte per the 2026 guideline).
- Behavior eval cases (`tests/eval-cases/`, 15 cases): schema tests passed; model-run scoring not yet performed.

Tested on 2026-08-10 on Windows with local Python 3.14 and Node.js runtimes.

## Release contract

- Plugin version: `2.0.0`.
- Bundled skills: exactly `write-school-records` and `korean-character-count`.
- The public achievement-standards corpus is not excluded by `.gitignore`.
- The plugin contains no ZIP artifacts, ZIP generation, generated checksum inventory, or external proofreading dependency.
- `SOURCE_METADATA.json` is a static provenance record and contains no local source path.

## Automated validation

- Official `plugin-creator` validator: passed.
- Official `skill-creator` quick validator: passed for both bundled skills.
- Package-specific verifier: passed.
- `PackageContractTests`: 10 passed.
- `write-school-records` development source: 94 passed.
- `write-school-records` package-local source: 87 passed after removing the redundant single-skill installer tests.

The package tests cover both manifests, the exact two-skill set, public metadata,
archive absence, dry-run behavior, install, verify, repeated install, uninstall,
and transactional rollback.

## Achievement-standards rights contract

- Common/core-course sources use `ncic_kogl_type_2` and `kogl_type_2`.
- Elective-course sources use `nkis_kogl_type_1` and `kogl_type_1`.
- Every public index names both `NCIC 국가교육과정정보센터` and `NKIS` and carries
  the Type 2/Type 1 reuse notice.
- `ATTRIBUTION.md` links the NCIC copyright policy and the NKIS research page.

## Deterministic character-count smoke test

Input `가A🙂` produced 3 graphemes, 1 line, and 8 bytes with the NEIS profile.
Text input, standard input, help, duplicate-input rejection, and invalid-profile
rejection all passed after adopting Node.js `util.parseArgs()`.

## Installation decision

- `manage_bundle.py` remains because this Git repository is a single plugin root,
  not a Codex marketplace wrapper containing `.agents/plugins/marketplace.json`
  and `plugins/korean-school-records-toolkit/`.
- `INSTALL.md` no longer claims that the missing marketplace wrapper is included.
- Claude Code local loading remains available through `claude --plugin-dir .`.

## Environment hygiene

- Official validators used a temporary project-local PyYAML directory; it was removed immediately after validation.
- No user skill installation path was changed.
- No real student data was used.
