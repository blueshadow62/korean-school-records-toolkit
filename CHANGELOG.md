# Changelog

## Unreleased

### Changed

- Relicense `write-school-records` from the restrictive internal-use notice to MIT, keeping the Copyright © 2026 blueshadow62 attribution.
- Relicense `write-school-records` again, from MIT to CC BY-NC-SA 4.0, and disclose the real author identity (© 2026 류기현, 부산 동아공고) in place of the `blueshadow62` handle. `korean-character-count` and `korean-spell-check` are unaffected (third-party sourced, remain MIT, no named copyright holder).
- Add a notice recommending users confirm their own 시도교육청 AI usage guidelines before use.

## 1.1.0 — 2026-07-30

### Added

- Add a Claude Code plugin manifest that reuses the existing three-skill layout.
- Add Claude Code personal installation and local validation instructions.
- Build a separate deterministic Claude Code ZIP without changing the three skill payloads.

### Unchanged

- Preserve the Codex plugin manifest, marketplace identity, and installation flow.
- Preserve all three skill names, behavior, scripts, references, and safety contracts.

## 1.0.1 — 2026-07-26

### Added

- Add the `write-school-records` copyright and authorized-internal-use notice.
- Add the recovered `korean-spell-check` P1–P10 fixture regression suite.

### Fixed

- Reject empty and whitespace-only spell-check input without a network request.
- Distinguish spell-check service failure from a successful check with no issues.
- Classify HTTP, network, parsing, and blocked-service failures.
- Normalize duplicate correction candidates while preserving order.

### Security / Safety

- Treat denied approval and incomplete inspection as unfinished, never as success or no spelling errors.
- Do not present the original text as a completed correction after service failure.

### Unchanged

- Preserve `write-school-records` functionality and active guidelines.
- Preserve the `korean-character-count` payload.
- Preserve the plugin ID, display name, and installation interface.

## 1.0.0 — 2026-07-24

- Package `write-school-records`, `korean-character-count`, and `korean-spell-check` as three independent skills in one Codex plugin.
- Add official plugin manifest and repo-local marketplace entry.
- Add transactional bundle management, package verification, integrity metadata, and installation guidance.
