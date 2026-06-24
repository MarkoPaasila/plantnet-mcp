"""Pl@ntNet API client."""

from __future__ import annotations

import mimetypes
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import httpx

from .location import resolve_location

API_BASE = "https://my-api.plantnet.org/v2/identify"
VALID_ORGANS = frozenset({"auto", "leaf", "flower", "fruit", "bark", "habit"})
VALID_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})
MAX_IMAGES = 5
TOP_RESULTS = 5
MAX_REFERENCE_IMAGES = 3


class PlantNetError(Exception):
    """Raised when identification fails."""


def validate_image_path(image_path: str) -> Path:
    path = Path(image_path).expanduser()
    if not path.exists():
        raise PlantNetError(f"Image not found: {image_path}")
    if not path.is_file():
        raise PlantNetError(f"Not a file: {image_path}")
    if path.suffix.lower() not in VALID_IMAGE_SUFFIXES:
        raise PlantNetError(
            "Image must be JPEG or PNG "
            f"(got {path.suffix or 'unknown extension'})"
        )
    return path


def validate_image_paths(image_paths: list[str]) -> list[Path]:
    if not image_paths:
        raise PlantNetError("At least one image path is required")
    if len(image_paths) > MAX_IMAGES:
        raise PlantNetError(f"At most {MAX_IMAGES} images are allowed per request")

    paths = [validate_image_path(path) for path in image_paths]
    return paths


def validate_organ(organ: str) -> str:
    value = (organ or "auto").strip().lower()
    if value not in VALID_ORGANS:
        allowed = ", ".join(sorted(VALID_ORGANS))
        raise PlantNetError(f"Invalid organ '{organ}'. Use one of: {allowed}")
    return value


def _resolve_organs(
    *,
    image_count: int,
    organ: str,
    organs: list[str] | None,
) -> list[str]:
    if organs is not None:
        if len(organs) != image_count:
            raise PlantNetError(
                f"organs length ({len(organs)}) must match image_paths length ({image_count})"
            )
        return [validate_organ(value) for value in organs]

    organ_value = validate_organ(organ)
    return [organ_value] * image_count


def _mime_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed in {"image/jpeg", "image/png"}:
        return guessed
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "image/png"


def _trim_image(entry: dict[str, Any]) -> dict[str, Any]:
    urls = entry.get("url") or {}
    original = urls.get("o")
    medium = urls.get("m")
    small = urls.get("s")
    return {
        "url": medium or original or small,
        "urls": {
            "original": original,
            "medium": medium,
            "small": small,
        },
        "organ": entry.get("organ"),
        "author": entry.get("author"),
        "license": entry.get("license"),
        "citation": entry.get("citation"),
    }


def _trim_species(entry: dict[str, Any]) -> dict[str, Any]:
    species = entry.get("species") or {}
    genus = species.get("genus") or {}
    family = species.get("family") or {}
    result = {
        "score": entry.get("score"),
        "scientificName": species.get("scientificName"),
        "scientificNameWithoutAuthor": species.get("scientificNameWithoutAuthor"),
        "scientificNameAuthorship": species.get("scientificNameAuthorship"),
        "commonNames": species.get("commonNames") or [],
        "genus": genus.get("scientificNameWithoutAuthor") or genus.get("scientificName"),
        "family": family.get("scientificNameWithoutAuthor") or family.get("scientificName"),
        "gbif": (entry.get("gbif") or {}).get("id"),
    }
    raw_images = entry.get("images")
    if raw_images:
        result["referenceImages"] = [
            _trim_image(image)
            for image in raw_images[:MAX_REFERENCE_IMAGES]
            if isinstance(image, dict)
        ]
    return result


def normalize_response(
    payload: dict[str, Any],
    top_n: int = TOP_RESULTS,
    location: dict[str, Any] | None = None,
) -> dict[str, Any]:
    results = [_trim_species(item) for item in (payload.get("results") or [])[:top_n]]
    predicted = []
    for item in payload.get("predictedOrgans") or []:
        predicted.append({
            "filename": item.get("filename"),
            "organ": item.get("organ"),
            "score": item.get("score"),
        })
    out = {
        "bestMatch": payload.get("bestMatch"),
        "project": (payload.get("query") or {}).get("project"),
        "language": payload.get("language"),
        "predictedOrgans": predicted,
        "results": results,
    }
    if location is not None:
        out["location"] = location
    return out


def identify_plant(
    *,
    image_paths: list[str],
    api_key: str,
    organ: str = "auto",
    organs: list[str] | None = None,
    project: str = "all",
    lang: str = "en",
    latitude: float | None = None,
    longitude: float | None = None,
    use_location: bool = True,
    include_reference_images: bool = False,
    timeout: float = 60.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Identify a plant from one or more local image files of the same individual."""
    key = (api_key or "").strip()
    if not key:
        raise PlantNetError(
            "PLANTNET_API_KEY not set. Get one at https://my.plantnet.org/settings/api-key"
        )

    paths = validate_image_paths(image_paths)
    organ_values = _resolve_organs(
        image_count=len(paths),
        organ=organ,
        organs=organs,
    )
    project_value = (project or "all").strip() or "all"
    lang_value = (lang or "en").strip() or "en"

    location_info: dict[str, Any] | None = None
    if use_location and project_value == "all":
        try:
            location_info = resolve_location(
                image_paths=paths,
                latitude=latitude,
                longitude=longitude,
                api_key=key,
                timeout=timeout,
                client=client,
            )
        except ValueError as exc:
            raise PlantNetError(str(exc)) from exc
        if location_info is not None:
            project_value = location_info["project"]

    url = f"{API_BASE}/{project_value}"
    params = {"api-key": key, "lang": lang_value}
    if include_reference_images:
        params["include-related-images"] = "true"

    with ExitStack() as stack:
        files = []
        for path, organ_value in zip(paths, organ_values):
            image_file = stack.enter_context(path.open("rb"))
            files.append(("organs", (None, organ_value)))
            files.append(("images", (path.name, image_file, _mime_type(path))))

        if client is not None:
            response = client.post(url, params=params, files=files)
        else:
            with httpx.Client(timeout=timeout) as http:
                response = http.post(url, params=params, files=files)

    if response.status_code in {401, 403}:
        raise PlantNetError("Invalid Pl@ntNet API key")
    if response.status_code == 429:
        raise PlantNetError("Pl@ntNet API rate limit exceeded; try again later")
    if response.status_code != 200:
        detail = response.text.strip()
        if len(detail) > 300:
            detail = detail[:300] + "..."
        raise PlantNetError(
            f"Pl@ntNet API error ({response.status_code})"
            + (f": {detail}" if detail else "")
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise PlantNetError("Pl@ntNet returned invalid JSON") from exc

    return normalize_response(payload, location=location_info)
