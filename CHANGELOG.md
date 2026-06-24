# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/MarkoPaasila/plantnet-mcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/MarkoPaasila/plantnet-mcp/releases/tag/v0.2.0
