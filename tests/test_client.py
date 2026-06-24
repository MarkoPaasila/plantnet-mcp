"""Tests for Pl@ntNet API client."""

import httpx
import pytest

from hermes_plantnet_plugin.client import (
    PlantNetError,
    identify_plant,
    normalize_response,
    validate_image_path,
    validate_image_paths,
    validate_organ,
)

SAMPLE_RESPONSE = {
    "query": {"project": "all", "images": ["abc"], "organs": ["auto"]},
    "language": "en",
    "bestMatch": "Rosa canina L.",
    "predictedOrgans": [
        {"filename": "flower.jpg", "organ": "flower", "score": 0.88},
    ],
    "results": [
        {
            "score": 0.91,
            "species": {
                "scientificName": "Rosa canina L.",
                "scientificNameWithoutAuthor": "Rosa canina",
                "scientificNameAuthorship": "L.",
                "commonNames": ["Dog rose"],
                "genus": {"scientificNameWithoutAuthor": "Rosa"},
                "family": {"scientificNameWithoutAuthor": "Rosaceae"},
            },
            "gbif": {"id": "3001234"},
        },
        {
            "score": 0.65,
            "species": {
                "scientificName": "Rosa rubiginosa L.",
                "scientificNameWithoutAuthor": "Rosa rubiginosa",
                "commonNames": ["Sweet briar"],
                "genus": {"scientificNameWithoutAuthor": "Rosa"},
                "family": {"scientificNameWithoutAuthor": "Rosaceae"},
            },
        },
    ],
}


def test_validate_organ_accepts_auto():
    assert validate_organ("auto") == "auto"
    assert validate_organ("FLOWER") == "flower"


def test_validate_organ_rejects_unknown():
    with pytest.raises(PlantNetError, match="Invalid organ"):
        validate_organ("root")


def test_validate_image_path_missing(tmp_path):
    with pytest.raises(PlantNetError, match="Image not found"):
        validate_image_path(str(tmp_path / "missing.jpg"))


def test_validate_image_path_wrong_type(tmp_path):
    bad = tmp_path / "note.txt"
    bad.write_text("not an image")
    with pytest.raises(PlantNetError, match="JPEG or PNG"):
        validate_image_path(str(bad))


def test_validate_image_paths_requires_at_least_one():
    with pytest.raises(PlantNetError, match="At least one image path"):
        validate_image_paths([])


def test_validate_image_paths_rejects_more_than_five(tmp_path):
    paths = []
    for index in range(6):
        image = tmp_path / f"plant{index}.jpg"
        image.write_bytes(b"\xff\xd8\xff\xd9")
        paths.append(str(image))

    with pytest.raises(PlantNetError, match="At most 5 images"):
        validate_image_paths(paths)


def test_normalize_response_trims_fields():
    out = normalize_response(SAMPLE_RESPONSE, top_n=2)
    assert out["bestMatch"] == "Rosa canina L."
    assert out["project"] == "all"
    assert len(out["results"]) == 2
    first = out["results"][0]
    assert first["scientificNameWithoutAuthor"] == "Rosa canina"
    assert first["commonNames"] == ["Dog rose"]
    assert first["genus"] == "Rosa"
    assert first["family"] == "Rosaceae"
    assert first["gbif"] == "3001234"
    assert out["predictedOrgans"][0]["organ"] == "flower"


def test_identify_plant_missing_api_key(tmp_path):
    image = tmp_path / "plant.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")
    with pytest.raises(PlantNetError, match="PLANTNET_API_KEY"):
        identify_plant(image_paths=[str(image)], api_key="")


def test_identify_plant_posts_multipart(tmp_path):
    image = tmp_path / "plant.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "/v2/identify/all" in str(request.url)
        assert request.url.params["api-key"] == "test-key"
        assert request.url.params["lang"] == "en"
        content_type = request.headers.get("content-type", "")
        assert "multipart/form-data" in content_type
        body = request.read().decode("latin-1")
        assert "plant.jpg" in body
        assert body.count('name="organs"') == 1
        assert body.count('name="images"') == 1
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    result = identify_plant(
        image_paths=[str(image)],
        api_key="test-key",
        organ="flower",
        client=client,
    )
    assert result["bestMatch"] == "Rosa canina L."
    assert result["results"][0]["score"] == 0.91


def test_identify_plant_posts_multiple_images(tmp_path):
    flower = tmp_path / "flower.jpg"
    leaf = tmp_path / "leaf.png"
    flower.write_bytes(b"\xff\xd8\xff\xd9")
    leaf.write_bytes(b"\x89PNG\r\n\x1a\n")

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode("latin-1")
        assert "flower.jpg" in body
        assert "leaf.png" in body
        assert body.count('name="images"') == 2
        assert body.count('name="organs"') == 2
        assert 'name="organs"' in body
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    result = identify_plant(
        image_paths=[str(flower), str(leaf)],
        api_key="test-key",
        organs=["flower", "leaf"],
        client=client,
    )
    assert result["bestMatch"] == "Rosa canina L."


def test_identify_plant_repeats_default_organ_for_each_image(tmp_path):
    images = []
    for name in ("one.jpg", "two.jpg"):
        path = tmp_path / name
        path.write_bytes(b"\xff\xd8\xff\xd9")
        images.append(str(path))

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode("latin-1")
        assert body.count('name="organs"') == 2
        assert body.count('name="images"') == 2
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    identify_plant(
        image_paths=images,
        api_key="test-key",
        organ="auto",
        client=client,
    )


def test_identify_plant_organs_length_mismatch(tmp_path):
    image = tmp_path / "plant.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")

    with pytest.raises(PlantNetError, match="organs length"):
        identify_plant(
            image_paths=[str(image)],
            api_key="test-key",
            organs=["flower", "leaf"],
        )


def test_identify_plant_http_errors(tmp_path):
    image = tmp_path / "plant.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    with pytest.raises(PlantNetError, match="Invalid Pl@ntNet API key"):
        identify_plant(image_paths=[str(image)], api_key="bad", client=client)


def test_identify_plant_rate_limit(tmp_path):
    image = tmp_path / "plant.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="too many requests")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    with pytest.raises(PlantNetError, match="rate limit"):
        identify_plant(image_paths=[str(image)], api_key="key", client=client)
