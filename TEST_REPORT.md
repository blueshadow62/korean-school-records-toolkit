# Test report

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
