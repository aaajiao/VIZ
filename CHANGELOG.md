# Changelog

All notable changes to this project are documented here.

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
