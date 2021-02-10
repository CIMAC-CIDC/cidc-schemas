# -*- coding: utf-8 -*-

"""Global test configuration and shared fixtures"""

import os
import sys
import logging

import pytest

from cidc_schemas.prism import set_prism_encrypt_key
from cidc_schemas.template import Template
from cidc_schemas.constants import SCHEMA_DIR, MANIFEST_DIR

set_prism_encrypt_key("")

# Set logger config to hide DEBUG statements for now
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@pytest.fixture
def pbmc_schema_path():
    return os.path.join(MANIFEST_DIR, "pbmc_template.json")


@pytest.fixture
def pbmc_template(pbmc_schema_path):
    return Template.from_json(pbmc_schema_path, SCHEMA_DIR)


@pytest.fixture
def tiny_template():
    """A small, valid """

    test_property = {
        "$id": "test_property",
        "type": "string",
        "merge_pointer": "test_property",
    }
    test_date = {"type": "string", "format": "date", "merge_pointer": "test_date"}
    test_time = {"type": "string", "format": "time", "merge_pointer": "test_time"}
    test_enum = {
        "type": "string",
        "enum": ["enum_val_1", "enum_val_2"],
        "merge_pointer": "test_enum",
    }
    test_number = {"type": "number", "merge_pointer": "test_number"}
    test_fields = {
        "test_property": test_property,
        "test_date": test_date,
        "test_time": test_time,
        "test_number": test_number,
        "test_enum": test_enum,
    }

    tiny_template_schema = {
        "$id": "tiny_template",
        "title": "Tiny Manifest",
        "properties": {
            "worksheets": {
                "TEST_SHEET": {
                    "preamble_rows": test_fields,
                    "data_columns": {
                        "first table": test_fields,
                        "another table": test_fields,
                    },
                }
            }
        },
    }

    return Template(tiny_template_schema, "test_tiny")
