"""Location extraction and Pl@ntNet project resolution from GPS coordinates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from PIL import Image

PROJECTS_API = "https://my-api.plantnet.org/v2/projects"
_GPS_IFD_TAG = 0x8825


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Validate WGS84 decimal coordinates."""
    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("latitude and longitude must be numbers") from exc

    if not -90 <= lat_value <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon_value <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return lat_value, lon_value


def _to_degrees(values: tuple[Any, ...]) -> float:
    degrees, minutes, seconds = values
    return float(degrees) + float(minutes) / 60 + float(seconds) / 3600


def extract_gps(path: Path) -> tuple[float, float] | None:
    """Read GPS coordinates from image EXIF, if present."""
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if not exif:
                return None
            gps_info = exif.get_ifd(_GPS_IFD_TAG)
            if not gps_info:
                return None

            lat_values = gps_info.get(2)
            lon_values = gps_info.get(4)
            if not lat_values or not lon_values:
                return None

            lat = _to_degrees(lat_values)
            lon = _to_degrees(lon_values)

            lat_ref = gps_info.get(1, "N")
            lon_ref = gps_info.get(3, "E")
            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon

            return validate_coordinates(lat, lon)
    except (OSError, ValueError):
        return None


def extract_gps_from_images(image_paths: list[Path]) -> tuple[float, float] | None:
    """Return GPS from the first image that contains valid coordinates."""
    for path in image_paths:
        coords = extract_gps(path)
        if coords is not None:
            return coords
    return None


def resolve_project_from_location(
    *,
    lat: float,
    lon: float,
    api_key: str,
    timeout: float = 30.0,
    client: httpx.Client | None = None,
) -> dict[str, str] | None:
    """Return the closest Pl@ntNet flora project for the given coordinates."""
    key = (api_key or "").strip()
    if not key:
        return None

    lat_value, lon_value = validate_coordinates(lat, lon)
    params = {"lat": lat_value, "lon": lon_value, "api-key": key}

    if client is not None:
        response = client.get(PROJECTS_API, params=params)
    else:
        with httpx.Client(timeout=timeout) as http:
            response = http.get(PROJECTS_API, params=params)

    if response.status_code != 200:
        return None

    try:
        projects = response.json()
    except ValueError:
        return None

    if not isinstance(projects, list) or not projects:
        return None

    first = projects[0]
    if not isinstance(first, dict) or not first.get("id"):
        return None

    return {
        "project": str(first["id"]),
        "title": str(first.get("title") or ""),
    }


def resolve_location(
    *,
    image_paths: list[Path],
    latitude: float | None = None,
    longitude: float | None = None,
    api_key: str,
    timeout: float = 30.0,
    client: httpx.Client | None = None,
) -> dict[str, Any] | None:
    """Resolve coordinates and the closest flora project slug."""
    source: str | None = None
    coords: tuple[float, float] | None = None

    if latitude is not None and longitude is not None:
        coords = validate_coordinates(latitude, longitude)
        source = "parameter"
    else:
        coords = extract_gps_from_images(image_paths)
        if coords is not None:
            source = "exif"

    if coords is None or source is None:
        return None

    lat_value, lon_value = coords
    project_info = resolve_project_from_location(
        lat=lat_value,
        lon=lon_value,
        api_key=api_key,
        timeout=timeout,
        client=client,
    )
    if project_info is None:
        return None

    return {
        "latitude": lat_value,
        "longitude": lon_value,
        "project": project_info["project"],
        "projectTitle": project_info["title"],
        "source": source,
    }
