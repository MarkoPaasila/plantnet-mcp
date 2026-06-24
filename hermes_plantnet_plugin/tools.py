"""Tool handlers — executed when the LLM calls each tool."""

import json
import os

from .client import PlantNetError, identify_plant


def _error(message: str) -> str:
    return json.dumps({"error": message})


def _parse_image_paths(args: dict) -> list[str]:
    raw = args.get("image_paths")
    if not isinstance(raw, list):
        raise PlantNetError("image_paths must be a non-empty array of 1 to 5 paths")

    paths = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise PlantNetError("image_paths must contain non-empty strings")
        paths.append(item.strip())

    if not paths:
        raise PlantNetError("image_paths must be a non-empty array of 1 to 5 paths")
    return paths


def _parse_organs(args: dict) -> list[str] | None:
    raw = args.get("organs")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise PlantNetError("organs must be an array when provided")
    return [str(item) for item in raw]


def _parse_optional_float(args: dict, key: str) -> float | None:
    raw = args.get(key)
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise PlantNetError(f"{key} must be a number")
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise PlantNetError(f"{key} must be a number") from exc


def plantnet_identify(args: dict, **kwargs) -> str:
    try:
        image_paths = _parse_image_paths(args)
    except PlantNetError as exc:
        return _error(str(exc))

    organ = args.get("organ") or "auto"
    project = args.get("project") or "all"
    lang = args.get("lang") or "en"
    include_reference_images = args.get("include_reference_images", True)
    use_location = args.get("use_location", True)
    api_key = os.environ.get("PLANTNET_API_KEY", "")

    try:
        latitude = _parse_optional_float(args, "latitude")
        longitude = _parse_optional_float(args, "longitude")
        if (latitude is None) != (longitude is None):
            raise PlantNetError("latitude and longitude must be provided together")
        organs = _parse_organs(args)
        result = identify_plant(
            image_paths=image_paths,
            api_key=api_key,
            organ=organ,
            organs=organs,
            project=project,
            lang=lang,
            latitude=latitude,
            longitude=longitude,
            use_location=bool(use_location),
            include_reference_images=bool(include_reference_images),
        )
        return json.dumps(result)
    except PlantNetError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"Plant identification failed: {exc}")
