"""Tests for extended AnvilCV JSON Schema generation.

Why:
    The JSON schema must include all Anvil-specific fields (anvil config,
    variant metadata) so editors can provide autocompletion for the full
    Anvil YAML format, not just rendercv fields.
"""

import json
import pathlib

from anvilcv.schema.json_schema import generate_json_schema, generate_json_schema_file


class TestJsonSchemaGeneration:
    def test_generates_valid_schema(self):
        schema = generate_json_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_schema_title_is_anvilcv(self):
        schema = generate_json_schema()
        assert schema["title"] == "AnvilCV"

    def test_schema_has_description(self):
        schema = generate_json_schema()
        assert "AnvilCV" in schema["description"]
        assert "rendercv" in schema["description"]

    def test_schema_has_anvil_field(self):
        schema = generate_json_schema()
        schema_json = json.dumps(schema)
        assert "anvil" in schema_json.lower()
        # The anvil field should be in the schema properties or definitions
        assert "AnvilConfig" in schema_json or "anvil" in schema_json

    def test_schema_has_variant_field(self):
        schema = generate_json_schema()
        schema_json = json.dumps(schema)
        assert "VariantMetadata" in schema_json or "variant" in schema_json

    def test_schema_has_cv_field(self):
        schema = generate_json_schema()
        # cv is the core rendercv field — must be present
        props = schema.get("properties", {})
        assert "cv" in props

    def test_schema_has_provider_config(self):
        schema = generate_json_schema()
        schema_json = json.dumps(schema)
        assert "anthropic" in schema_json
        assert "openai" in schema_json
        assert "ollama" in schema_json

    def test_schema_has_github_config(self):
        schema = generate_json_schema()
        schema_json = json.dumps(schema)
        assert "GitHubConfig" in schema_json or "github" in schema_json

    def test_schema_serializes_to_json(self):
        schema = generate_json_schema()
        json_str = json.dumps(schema, indent=2, ensure_ascii=False)
        assert len(json_str) > 100
        # Verify round-trip
        parsed = json.loads(json_str)
        assert parsed["title"] == "AnvilCV"


class TestJsonSchemaFile:
    def test_writes_schema_file(self, tmp_path: pathlib.Path):
        output = tmp_path / "schema.json"
        result = generate_json_schema_file(output)
        assert result == output
        assert output.exists()

        content = json.loads(output.read_text())
        assert content["title"] == "AnvilCV"

    def test_creates_parent_dirs(self, tmp_path: pathlib.Path):
        output = tmp_path / "nested" / "dir" / "schema.json"
        generate_json_schema_file(output)
        assert output.exists()

    def test_file_is_valid_json(self, tmp_path: pathlib.Path):
        output = tmp_path / "schema.json"
        generate_json_schema_file(output)
        # Should not raise
        json.loads(output.read_text(encoding="utf-8"))
