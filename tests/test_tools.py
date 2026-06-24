"""Tests for plantnet_identify tool handler."""

import json
from unittest.mock import patch

from hermes_plantnet_plugin.tools import plantnet_identify


def test_plantnet_identify_missing_paths():
    out = json.loads(plantnet_identify({}))
    assert "error" in out
    assert "image_paths" in out["error"].lower()


def test_plantnet_identify_rejects_empty_paths():
    out = json.loads(plantnet_identify({"image_paths": []}))
    assert "error" in out
    assert "image_paths" in out["error"].lower()


def test_plantnet_identify_success(tmp_path, monkeypatch):
    image = tmp_path / "leaf.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")
    monkeypatch.setenv("PLANTNET_API_KEY", "test-key")

    fake_result = {
        "bestMatch": "Taraxacum officinale F.H.Wigg.",
        "project": "all",
        "language": "en",
        "predictedOrgans": [],
        "results": [{"score": 0.95, "scientificNameWithoutAuthor": "Taraxacum officinale"}],
    }

    with patch(
        "hermes_plantnet_plugin.tools.identify_plant",
        return_value=fake_result,
    ) as mock_identify:
        out = json.loads(
            plantnet_identify({
                "image_paths": [str(image)],
                "organ": "leaf",
                "project": "weurope",
            })
        )

    mock_identify.assert_called_once_with(
        image_paths=[str(image)],
        api_key="test-key",
        organ="leaf",
        organs=None,
        project="weurope",
        lang="en",
    )
    assert out["bestMatch"] == "Taraxacum officinale F.H.Wigg."


def test_plantnet_identify_multiple_paths(tmp_path, monkeypatch):
    flower = tmp_path / "flower.jpg"
    leaf = tmp_path / "leaf.jpg"
    flower.write_bytes(b"\xff\xd8\xff\xd9")
    leaf.write_bytes(b"\xff\xd8\xff\xd9")
    monkeypatch.setenv("PLANTNET_API_KEY", "test-key")

    fake_result = {"bestMatch": "Rosa canina L.", "results": []}

    with patch(
        "hermes_plantnet_plugin.tools.identify_plant",
        return_value=fake_result,
    ) as mock_identify:
        plantnet_identify({
            "image_paths": [str(flower), str(leaf)],
            "organs": ["flower", "leaf"],
        })

    mock_identify.assert_called_once_with(
        image_paths=[str(flower), str(leaf)],
        api_key="test-key",
        organ="auto",
        organs=["flower", "leaf"],
        project="all",
        lang="en",
    )


def test_plantnet_identify_propagates_client_error(tmp_path, monkeypatch):
    image = tmp_path / "leaf.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")
    monkeypatch.setenv("PLANTNET_API_KEY", "test-key")

    from hermes_plantnet_plugin.client import PlantNetError

    with patch(
        "hermes_plantnet_plugin.tools.identify_plant",
        side_effect=PlantNetError("Invalid Pl@ntNet API key"),
    ):
        out = json.loads(plantnet_identify({"image_paths": [str(image)]}))

    assert out["error"] == "Invalid Pl@ntNet API key"
