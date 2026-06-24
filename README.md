# hermes-plantnet-plugin

Hermes Agent plugin for identifying plants from photos using the [Pl@ntNet API](https://my.plantnet.org/).

**Version:** `0.3.0` — see [Changelog](CHANGELOG.md)

## Tool

| Tool | Description |
|------|-------------|
| `plantnet_identify` | Identify a plant species from 1–5 local JPEG/PNG images of the same plant |

Bundled skill: `plantnet:plantnet` (load with `skill_view`).

## Prerequisites

1. **Pl@ntNet API key** from [my.plantnet.org/settings/api-key](https://my.plantnet.org/settings/api-key)
2. Add to `~/.hermes/.env`:
   ```
   PLANTNET_API_KEY=your-key-here
   ```

## Install

### From GitHub (recommended)

```bash
hermes plugins install MarkoPaasila/plantnet-mcp --enable
```

Or with the full Git URL:

```bash
hermes plugins install https://github.com/MarkoPaasila/plantnet-mcp --enable
```

If you use the Hermes gateway, restart it after install: `hermes gateway restart`.

### Local clone (development)

```bash
git clone https://github.com/MarkoPaasila/plantnet-mcp.git
cd plantnet-mcp
hermes plugins install "$(pwd)" --enable
```

### Pip (development)

```bash
cd /path/to/plantnet-mcp
pip install -e .
hermes plugins enable plantnet
```

### Symlink (development)

```bash
ln -s "$(pwd)" ~/.hermes/plugins/plantnet
hermes plugins enable plantnet
```

Pip entry-point plugins are opt-in; you must run `hermes plugins enable plantnet` after install.

## Usage

Send plant photo(s) via CLI or Telegram and ask Hermes to identify them:

```bash
hermes chat --image flower.jpg -q "What plant is this?"
```

For multiple images, use interactive `hermes chat` and attach several files before sending, or on Telegram send a **photo album** (up to 5) with your question in the caption:

> What plant is this?

Hermes attaches images with path hints like `[Image attached at: /home/user/.hermes/cache/images/...]`. The agent calls `plantnet_identify` with all paths from the message.

### Tool parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `image_paths` | required | 1–5 local JPEG/PNG paths from image hints (same plant) |
| `organ` | `auto` | Organ for all images when `organs` is omitted |
| `organs` | — | Optional per-image organ list (`leaf`, `flower`, etc.) |
| `project` | `all` | Flora project (`weurope`, `canada`, etc.) |
| `lang` | `en` | Language for common names |

### Breaking change (0.2.0)

`image_path` (single string) was replaced by `image_paths` (array). Pass one path as a single-element array.

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

GPL-2.0-only — see [LICENSE](LICENSE).
