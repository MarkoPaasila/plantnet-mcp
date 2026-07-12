# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2026-07-12

### Fixed

- Plugin failed to load under Hermes' directory-plugin loader (`No module named 'hermes_plantnet_plugin'`), leaving `plantnet_identify` unregistered. Root cause: plugin-root shims used absolute imports `from hermes_plantnet_plugin...`, but the loader imports the plugin as the `plantnet` package, so the subpackage is only reachable as `plantnet.hermes_plantnet_plugin`. Switched the shims to relative imports `from .hermes_plantnet_plugin...`.

## [0.5.0] - 2026-06-24

### Added

- Location-aware flora project resolution: when `project` is `all`, GPS from image EXIF or optional `latitude`/`longitude` parameters are used to pick the closest Pl@ntNet flora via `/v2/projects`.
- Optional `use_location` parameter (default `true`) to disable auto-resolution and force worldwide `all`.
- `location` block in identification results when coordinates were used (project, title, source).
- `Pillow` dependency for EXIF GPS extraction.

## [0.4.0] - 2026-06-24

### Added

- `include_reference_images` parameter on `plantnet_identify` (default `true`): returns Pl@ntNet database reference photo URLs with attribution metadata for each identification result.

## [0.3.0] - 2026-06-24

### Changed

- Align directory layout with the Hermes Agent plugin protocol: `plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`, and `skills/` at the plugin root.
- Move bundled skill to plugin-root `skills/plantnet/`; register from root or pip package via symlink.

## [0.2.0] - 2026-06-24

### Added

- Hermes Agent plugin for plant identification via the [Pl@ntNet API](https://my.plantnet.org/).
- `plantnet_identify` tool: identify a species from 1–5 local JPEG/PNG images of the same plant.
- Optional `organ` (default `auto`), per-image `organs`, `project` (flora region), and `lang` parameters.
- Bundled `plantnet` skill for agent guidance (`plantnet:plantnet`).
- `PLANTNET_API_KEY` environment check before the tool is offered.
- Tests for the API client and tool handler.

### Changed

- **Breaking:** `image_path` (single string) replaced by `image_paths` (array of 1–5 paths). Pass a single image as a one-element array.

[Unreleased]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/MarkoPaasila/plantnet-mcp/releases/tag/v0.2.0
