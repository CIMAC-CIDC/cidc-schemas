#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for data model schemas."""

import os
import pytest
import json
import jsonschema

from cidc_schemas.json_validation import load_and_validate_schema


def example_paths():
    """Get the path to every .json in the 'data/clinicaltrial_examples' directory"""
    for root, _, paths in os.walk(
        os.path.join(os.path.dirname(__file__), "data/clinicaltrial_examples")
    ):
        for path in paths:
            if not path.endswith(".json"):
                continue

            yield root, path


@pytest.mark.parametrize("example_path", example_paths(), ids=lambda x: x[1])
def test_schema(example_path):
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    full_path = os.path.join(*example_path)
    _, fname = example_path

    with open(full_path) as file:
        try:
            ct_example = json.load(file)
        except Exception as e:
            raise Exception(f"Error decoding {example_path}: {e}")

        try:
            validator.validate(ct_example)
        except jsonschema.exceptions.ValidationError as e:
            raise Exception(
                f'Failed to validate {fname}:{"["+"][".join(repr(p) for p in e.absolute_path)+"]"} \
                \n {e.message} \
                \n CT_SCHEMA{"["+"][".join(repr(p) for p in e.absolute_schema_path)+"]"} \
                \n instance {e.instance}'
            )
