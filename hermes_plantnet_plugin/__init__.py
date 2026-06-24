"""Pl@ntNet plant identification plugin for Hermes Agent."""

import logging
import os
from pathlib import Path

from . import schemas, tools
from ._version import __version__

__all__ = ["register", "__version__"]

logger = logging.getLogger(__name__)

_TOOLSET = "plantnet"


def _plugin_ready() -> bool:
    return bool(os.environ.get("PLANTNET_API_KEY", "").strip())


def _skills_dir() -> Path:
    """Prefer plugin-root skills/ (Hermes directory layout), then package skills/."""
    plugin_root = Path(__file__).resolve().parent.parent
    root_skills = plugin_root / "skills"
    if root_skills.is_dir():
        return root_skills
    return Path(__file__).resolve().parent / "skills"


def register(ctx):
    """Wire schemas to handlers and bundle the plantnet skill."""
    ctx.register_tool(
        name="plantnet_identify",
        toolset=_TOOLSET,
        schema=schemas.PLANTNET_IDENTIFY,
        handler=tools.plantnet_identify,
        check_fn=_plugin_ready,
    )

    skills_dir = _skills_dir()
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.is_file():
                ctx.register_skill(child.name, skill_md)

    logger.debug("plantnet plugin registered")
