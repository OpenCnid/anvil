"""Extended JSON Schema generation for AnvilCV.

Why:
    The vendored rendercv schema generator produces a schema for RenderCVModel
    only. This module generates an extended schema from AnvilModel, which
    includes all Anvil-specific fields (anvil config, variant metadata) while
    retaining full rendercv compatibility.
"""

from __future__ import annotations

import json
import pathlib

import pydantic

from anvilcv.schema.anvil_model import AnvilModel


def generate_json_schema() -> dict:
    """Generate JSON Schema (Draft-07) from AnvilModel.

    Returns a schema that covers both rendercv fields and Anvil extensions.
    """

    class AnvilSchemaGenerator(pydantic.json_schema.GenerateJsonSchema):
        def generate(self, schema, mode="validation"):
            json_schema = super().generate(schema, mode=mode)
            json_schema["title"] = "AnvilCV"
            json_schema["description"] = (
                "AnvilCV resume schema — extends rendercv with AI tailoring, "
                "ATS scoring, GitHub integration, and variant tracking."
            )
            json_schema["$id"] = (
                "https://raw.githubusercontent.com/anvilcv/anvilcv/main/schema.json"
            )
            json_schema["$schema"] = "http://json-schema.org/draft-07/schema#"
            return json_schema

    return AnvilModel.model_json_schema(schema_generator=AnvilSchemaGenerator)


def generate_json_schema_file(output_path: pathlib.Path) -> pathlib.Path:
    """Generate and save AnvilCV JSON Schema to file.

    Args:
        output_path: Target file path for schema output.

    Returns:
        Path to the written schema file.
    """
    schema = generate_json_schema()
    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(schema_json, encoding="utf-8")
    return output_path
