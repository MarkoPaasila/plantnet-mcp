---
name: plantnet
description: >-
  Identify plants from photos using the Pl@ntNet API via the plantnet_identify
  tool. Use when the user sends plant image(s) or asks what species a plant is.
---

# Pl@ntNet plant identification (Hermes plugin)

## Requirements

- **`PLANTNET_API_KEY`** in `~/.hermes/.env` (get one at https://my.plantnet.org/settings/api-key)
- Plugin enabled: `hermes plugins enable plantnet`

Always use **`plantnet_identify`** for species identification. Do not guess species from vision alone when this tool is available.

No manual skill invocation is needed for normal use — send photos and ask your question in the same message.

## When to use

- User attaches one or more plant photos (CLI, Telegram, or other channel)
- User asks "what plant is this?", "identify this flower", etc.
- User wants scientific or common names with confidence scores

## Image paths

Hermes adds one hint per attached image, e.g. `[Image attached at: /home/user/.hermes/cache/images/abc.jpg]`.

Collect **all** local `[Image attached at: ...]` hints from the **current user message** into `image_paths` when they show the same plant (1 to 5 images). Use only local file paths — not remote `[Image attached: https://...]` URLs.

### Telegram workflow (recommended)

1. Select up to 5 photos of the **same plant** (flower + leaf improves accuracy).
2. Send as a **Telegram album** with a caption such as "What plant is this?"
3. Pass every path from that message to `plantnet_identify` in one call.

Rapid separate photos sent within about a second are also merged into one Hermes turn. Photos sent slowly in separate messages are **not** combined — ask the user to resend as an album if they want multi-image identification.

If images clearly show **different plants**, ask the user or run separate identifications.

### CLI workflow

In interactive `hermes chat`, attach multiple images via `/image` or paste, then send one prompt. One-shot `hermes chat --image` only supports a single file.

## Tool parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `image_paths` | required | 1–5 paths from `[Image attached at: ...]` hints (same plant) |
| `organ` | `auto` | Applied to every image unless `organs` is set |
| `organs` | — | Optional per-image organ list (same length as `image_paths`) |
| `project` | `all` | Flora region; see below |
| `lang` | `en` | Language for common names |

For casual identification, `organ=auto` and `project=all` are fine.

### Organ values

- **auto** — let Pl@ntNet detect the plant part (recommended default)
- **leaf** — foliage, needles, or fronds
- **flower** — blooms, inflorescences
- **fruit** — berries, seed pods, cones with seeds
- **bark** — trunk or stem bark texture
- **habit** — whole-plant growth form

Set `organ` when every image shows the same part. Use `organs` when the user labels different parts per photo (e.g. `["flower", "leaf"]`).

### Project (flora region)

Use `project=all` unless the user specifies a region or you know the photo location:

| Project | Region |
|---------|--------|
| `all` | Worldwide (default) |
| `weurope` | Western Europe |
| `canada` | Canada |
| `useful` | Useful plants |

More flora lists: https://my.plantnet.org/doc/newfloras

## Presenting results

1. State **`bestMatch`** as the top suggestion.
2. Show the top 3 **`results`** with confidence (`score` as percentage).
3. Include **common names** when present, plus scientific name.
4. Mention close alternatives when scores are similar (user may need a clearer photo).
5. Note **`predictedOrgans`** if Pl@ntNet detected a different organ than expected.

Example phrasing: "Most likely *Rosa canina* (dog rose) — 91% confidence. Alternatives: *Rosa rubiginosa* (78%), *Rosa arvensis* (65%)."

## Limitations

- JPEG and PNG only; 1 to 5 images per call, all must be the same plant individual.
- Results are probabilistic; low scores mean uncertain identification.
- Regional `project` improves accuracy when the plant is from that flora.
- Slow Telegram album downloads may occasionally split images across separate agent turns (Hermes limitation).
