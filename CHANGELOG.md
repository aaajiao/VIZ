# Changelog

All notable changes to this project are documented here.

## 0.7.0 - 2026-04-10

### Breaking Changes

- All error paths now exit with code 1 (previously exited 0 with JSON `status: error`). Callers that only check `status` field are unaffected; callers that relied on exit code 0 will now correctly see failures.
- Malformed stdin JSON is now a fatal error (exit 1). Previously the CLI silently continued with empty input.
- `output_schema` in `capabilities` is now per-command (`generate` / `convert`), no longer a flat dict.
- Removed dead `meta` field from `make_content()` content dict.

### Added

- `--color-scheme` CLI argument for `generate` (previously only available via stdin JSON).
- `sdf_masked` composition mode exposed in CLI `--composition` choices and `capabilities` output (was already supported by the grammar engine at ~12% probability).
- Sanitization warnings: when inputs are clamped (duration, fps, width, height) or truncated (headline, title, body, metrics), the `generate` output JSON includes a `warnings` list describing what changed.
- `_VALID_COMPOSITION_MODES` module-level constant; capabilities now derives layouts, decorations, blend modes, and composition modes dynamically from `_VALID_*` constants instead of hardcoded lists.
- Strict `--palette` validation: non-numeric values and fewer than 2 triplets produce structured errors instead of crashes.
- `_parse_compound_arg` rejects empty strings and missing type names with `ValueError`.

### Changed

- Skill `SKILL.md` slimmed from 241 to 90 lines as a minimal agent protocol. Detailed content moved to `references/VISUAL_OPTIONS.md` (new) and existing reference files. Agent loads references on demand instead of all at once.

### Documentation

- All docs (usage, ai-integration, AGENTS, README, skill references) aligned with new error/warning semantics, `sdf_masked`, `--color-scheme`, and per-command `output_schema`.
- Fixed missing `--output-dir` in `docs/usage.md` convert examples and `README.md` Director Mode example.

### Testing

- 36 new tests: exit codes for all error paths, malformed stdin JSON, bad VAD (3 variants), bad palette (3 variants), sanitization warnings, `--color-scheme` CLI, `sdf_masked` composition (unit + CLI + capabilities), `_parse_compound_arg` edge cases, `meta` field removal, `_warnings` coverage for all clamp/truncation scenarios.

## 0.6.5 - 2026-03-17

### Documentation

- Added a top-level `CHANGELOG.md`.
- Added release notes links to the README install section.
- Added `Releases` and `Changelog` project URLs for PyPI metadata.

## 0.6.4 - 2026-03-17

### Changed

- `viz generate` and `viz convert` now require an explicit `--output-dir`.
- The CLI no longer falls back to `./media`, preventing ambiguous output locations after install.

### Documentation

- Updated README examples to use explicit output directories.
- Updated `docs/usage.md` and `docs/ai-integration.md` for the new CLI requirement.
- Updated the bundled `viz-ascii-art` skill and references to use `--output-dir`.

### Testing

- Added CLI coverage for missing `--output-dir` failure cases.
