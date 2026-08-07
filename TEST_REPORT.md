# Test report

Tested on 2026-07-26 and 2026-07-30 (Windows, local Python and Node.js runtimes).

## Package validation

- Official `plugin-creator` validator: passed for 1.0.1. The 1.1.0 rerun was unavailable because the current Python environment does not contain its `yaml` dependency.
- Package-specific manifest, checksum, release-contract, secret-pattern, privacy-path, cache, and executable-path checks: passed.
- `PackageContractTests`: 10 passed.
  - Three independent skills are present with unique names.
  - Version `1.1.0`, both platform manifests, the approved `write-school-records` notice, and the spell-check fixture set are enforced.
  - The Claude Code ZIP has `.claude-plugin/plugin.json` and the three shared skill directories at its root, without Codex marketplace files.
  - Public metadata excludes local source paths.
  - Dry run leaves the destination unchanged.
  - Install, verify, repeated install, uninstall, and rollback work in a temporary directory.
  - A simulated failure while committing the second skill restores all three prior installations.
  - A corrupted packaged file is rejected.

## Bundled skill regression checks

- `write-school-records`: 75 tests passed, including 27 integration-contract tests.
  - Active guideline verification passed for `2026_2026-02-12`.
  - `current.md` SHA-256 remains `B087236E5795C97C566F1F502DB2E5CC88C60EEEA2562C01F9548DF2273FE343`.
  - The only added component file is `LICENSE`; functional files match the development baseline.
- `korean-character-count`: deterministic smoke checks passed.
  - Mixed Hangul, English, digits, spaces, punctuation, and a line break: default `15` characters, `23` UTF-8 bytes, `2` lines.
  - The same input with the NEIS profile: `15` characters, `24` profile bytes, `2` lines.
  - `501` Hangul characters produce `1503` NEIS-profile bytes and correctly exceed `1500`.
- `korean-spell-check`: P1–P10 fixture tests passed (`10/10`).
  - Empty and whitespace-only input make zero network requests and exit with code `1`.
  - HTTP, network, parsing, and blocked-service failures are distinct.
  - Duplicate correction candidates are normalized while preserving order.
  - Live synthetic check succeeded: `할수있는` was reported as `할 수 있는`.
  - A second live synthetic student-record-style sentence completed with zero issues and preserved the source facts and sentence style.

## Integrated synthetic smoke

Synthetic evidence only:

> The student graphed speed and braking-distance data, set a quadratic expression, identified a model limitation, and revised axis units and the explanation after feedback.

Generated draft:

> 속도와 제동 거리 자료를 그래프로 나타내고 이차함수 식을 설정함. 실제 자료와 모형의 차이를 지적하고, 피드백을 반영해 그래프 축 단위와 식의 설명을 수정함.

Results:

- No unsupported presentation, collaboration, achievement, leadership, or career claim was added.
- Internal A–D codes were not exposed.
- The spell-check service returned zero issues; the text and evaluation strength remained unchanged.
- Final `analyze_record.py`: `88` code points and `216` UTF-8 bytes, with no warnings.
- Final character-count NEIS profile: `88` graphemes and `216` bytes.
- A single-function request remains independently routable; the plugin does not force unrelated skills.

## Temporary installation

- Dry run, install, verify, idempotent reinstall, uninstall, rollback, and post-rollback verify: passed.
- Post-rollback entry-point smoke checks passed for all three skills.
- No actual user installation path was changed.

## Source and safety

- `korean-spell-check` normalized source/package tree SHA-256: `01bfc0316e0dff7a29ec6d985b7d014ed76f23c3d5448f0d1c83e2352e085b82`.
- `korean-character-count` uses the unchanged 1.0.0 source selection.
- Public release metadata contains no user-specific absolute source paths; local reproduction paths are stored only in `SOURCE_METADATA.local.json`, which is excluded from the ZIP.
- Fixture files contain no cookies, session identifiers, tokens, live response dumps, or student data.
- The external spell-check surface remains a network and policy dependency. Denied approval or service failure must be reported as incomplete inspection, never as success or no spelling errors.

## Release archive

- Deterministic 1.0.1 two-build SHA-256 comparison: passed.
- ZIP extraction, checksum verification, marketplace parsing, and extracted official validator: passed.
- `SOURCE_METADATA.local.json` is absent from the public ZIP.
- Existing `1.0.0` ZIP preservation check passed with SHA-256 `D8E7B9ED27CD4DD20334306061D86BD32242F108CA634473D5906D2B0EC92291`.

## Claude Code packaging

- `.claude-plugin/plugin.json` JSON parsing and package-specific schema checks: passed.
- The existing `skills/<name>/SKILL.md` layout is reused without duplicating or changing any skill payload.
- Claude Code local validation and `--plugin-dir` commands are documented in `README_CLAUDE_CODE.md`.
- The official `claude plugin validate . --strict` command was not executed because Claude Code is not installed in this environment.
- A separate deterministic Claude Code ZIP is generated so the Codex marketplace archive remains independently installable.
