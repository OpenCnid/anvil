"""Anvil model builder — wraps vendored rendercv_model_builder.

Why:
    The vendored builder validates YAML and builds RenderCVModel. We wrap it
    to build AnvilModel instead, which adds the `anvil` section. The wrapper
    calls the same pipeline (YAML merge, overlay handling, CLI overrides) but
    validates against AnvilModel rather than RenderCVModel.

    This is a Wrapped file — we do NOT modify the vendored builder. We call
    its functions and substitute our model class.
"""

from __future__ import annotations

import pathlib
from typing import Any, Unpack

import pydantic
from ruamel.yaml.comments import CommentedMap

from anvilcv.schema.anvil_model import AnvilModel
from anvilcv.vendor.rendercv.exception import (
    RenderCVUserValidationError,
)
from anvilcv.vendor.rendercv.schema.models.validation_context import ValidationContext
from anvilcv.vendor.rendercv.schema.pydantic_error_handling import (
    parse_validation_errors,
)
from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
    BuildRendercvModelArguments,
    build_rendercv_dictionary,
)


def build_anvil_model_from_commented_map(
    commented_map: CommentedMap | dict[str, Any],
    input_file_path: pathlib.Path | None = None,
    overlay_sources: dict[str, CommentedMap] | None = None,
) -> AnvilModel:
    """Validate merged dictionary and build AnvilModel.

    Same as vendored build_rendercv_model_from_commented_map but uses
    AnvilModel instead of RenderCVModel, allowing the `anvil` section.
    """
    try:
        validation_context = {
            "context": ValidationContext(
                input_file_path=input_file_path,
                current_date=commented_map.get("settings", {}).get(
                    "current_date", "today"
                ),
            )
        }
        model = AnvilModel.model_validate(
            commented_map, context=validation_context
        )
    except pydantic.ValidationError as e:
        validation_errors = parse_validation_errors(
            e, commented_map, overlay_sources
        )
        raise RenderCVUserValidationError(validation_errors) from e

    return model


def build_anvil_dictionary_and_model(
    main_yaml_file: str,
    *,
    input_file_path: pathlib.Path | None = None,
    **kwargs: Unpack[BuildRendercvModelArguments],
) -> tuple[CommentedMap, AnvilModel]:
    """Complete pipeline from raw YAML string to validated AnvilModel.

    Reuses vendored build_rendercv_dictionary for YAML merging/overlay
    handling, then validates with AnvilModel instead of RenderCVModel.
    """
    d, overlay_sources = build_rendercv_dictionary(main_yaml_file, **kwargs)
    m = build_anvil_model_from_commented_map(d, input_file_path, overlay_sources)
    return d, m
