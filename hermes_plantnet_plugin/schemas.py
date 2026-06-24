"""Tool schemas — what the LLM sees."""

_ORGAN_ENUM = ["auto", "leaf", "flower", "fruit", "bark", "habit"]

PLANTNET_IDENTIFY = {
    "name": "plantnet_identify",
    "description": (
        "Identify a plant species from one or more local images (same individual) "
        "using the Pl@ntNet API. Use when the user sends plant photo(s) or asks "
        "what species a plant is. Pass all paths from [Image attached at: ...] hints "
        "in the user message."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 5,
                "description": (
                    "1 to 5 absolute or home-relative paths to JPEG or PNG images "
                    "of the same plant (from [Image attached at: ...] hints)"
                ),
            },
            "organ": {
                "type": "string",
                "description": (
                    "Plant part shown in every image when organs is omitted: auto, "
                    "leaf, flower, fruit, bark, or habit. Default auto lets Pl@ntNet "
                    "detect the organ per image."
                ),
                "enum": _ORGAN_ENUM,
            },
            "organs": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": _ORGAN_ENUM,
                },
                "minItems": 1,
                "maxItems": 5,
                "description": (
                    "Optional per-image organ values, one per image_paths entry in "
                    "the same order. Overrides organ when provided."
                ),
            },
            "project": {
                "type": "string",
                "description": (
                    "Flora project slug for regional species lists. "
                    "Use 'all' for worldwide flora, or e.g. weurope, canada."
                ),
            },
            "lang": {
                "type": "string",
                "description": (
                    "Language code for common names in results (default en)."
                ),
            },
        },
        "required": ["image_paths"],
    },
}
