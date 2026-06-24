"""Tests for location extraction and project resolution."""

from pathlib import Path

import httpx
import piexif
import pytest
from PIL import Image

from hermes_plantnet_plugin.location import (
    extract_gps,
    extract_gps_from_images,
    resolve_location,
    resolve_project_from_location,
    validate_coordinates,
)

PROJECTS_RESPONSE = [
    {
        "id": "k-southwestern-europe",
        "title": "Southwestern Europe",
        "description": "Plants of Southwestern Europe",
        "speciesCount": 7248,
    },
    {
        "id": "cevennes",
        "title": "Cévennes",
        "description": "Flora of the Cévennes National Park",
        "speciesCount": 2392,
    },
]


def _deg_to_dms_rational(decimal: float) -> tuple[tuple[int, int], ...]:
    degrees = int(abs(decimal))
    minutes_float = (abs(decimal) - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60 * 10000)
    return ((degrees, 1), (minutes, 1), (seconds, 10000))


def write_gps_jpeg(path: Path, lat: float, lon: float) -> None:
    """Create a minimal JPEG with embedded GPS EXIF."""
    img = Image.new("RGB", (8, 8), color=(0, 128, 0))
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: _deg_to_dms_rational(lat),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: _deg_to_dms_rational(lon),
    }
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    img.save(path, exif=exif_bytes)


def test_validate_coordinates_accepts_valid_values():
    lat, lon = validate_coordinates(43.451, 3.145)
    assert lat == pytest.approx(43.451)
    assert lon == pytest.approx(3.145)


def test_validate_coordinates_rejects_out_of_range():
    with pytest.raises(ValueError, match="latitude"):
        validate_coordinates(91, 0)
    with pytest.raises(ValueError, match="longitude"):
        validate_coordinates(0, 181)


def test_validate_coordinates_rejects_non_numeric():
    with pytest.raises(ValueError, match="numbers"):
        validate_coordinates("north", 3.0)  # type: ignore[arg-type]


def test_extract_gps_reads_exif(tmp_path):
    image = tmp_path / "gps.jpg"
    write_gps_jpeg(image, 43.451, 3.145)
    coords = extract_gps(image)
    assert coords is not None
    lat, lon = coords
    assert lat == pytest.approx(43.451, abs=0.001)
    assert lon == pytest.approx(3.145, abs=0.001)


def test_extract_gps_returns_none_without_gps(tmp_path):
    image = tmp_path / "plain.jpg"
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(image)
    assert extract_gps(image) is None


def test_extract_gps_from_images_uses_first_with_gps(tmp_path):
    plain = tmp_path / "plain.jpg"
    gps = tmp_path / "gps.jpg"
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(plain)
    write_gps_jpeg(gps, 60.17, 24.94)

    coords = extract_gps_from_images([plain, gps])
    assert coords is not None
    lat, lon = coords
    assert lat == pytest.approx(60.17, abs=0.01)
    assert lon == pytest.approx(24.94, abs=0.01)


def test_resolve_project_from_location_picks_closest():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert "/v2/projects" in str(request.url)
        assert request.url.params["lat"] == "43.451"
        assert request.url.params["lon"] == "3.145"
        return httpx.Response(200, json=PROJECTS_RESPONSE)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = resolve_project_from_location(
        lat=43.451,
        lon=3.145,
        api_key="test-key",
        client=client,
    )
    assert result == {
        "project": "k-southwestern-europe",
        "title": "Southwestern Europe",
    }


def test_resolve_project_from_location_returns_none_on_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert resolve_project_from_location(
        lat=43.451,
        lon=3.145,
        api_key="test-key",
        client=client,
    ) is None


def test_resolve_location_from_parameters():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PROJECTS_RESPONSE)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = resolve_location(
        image_paths=[],
        latitude=43.451,
        longitude=3.145,
        api_key="test-key",
        client=client,
    )
    assert result == {
        "latitude": 43.451,
        "longitude": 3.145,
        "project": "k-southwestern-europe",
        "projectTitle": "Southwestern Europe",
        "source": "parameter",
    }


def test_resolve_location_from_exif(tmp_path):
    image = tmp_path / "gps.jpg"
    write_gps_jpeg(image, 43.451, 3.145)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PROJECTS_RESPONSE)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = resolve_location(
        image_paths=[image],
        api_key="test-key",
        client=client,
    )
    assert result is not None
    assert result["source"] == "exif"
    assert result["project"] == "k-southwestern-europe"
    assert result["latitude"] == pytest.approx(43.451, abs=0.001)
