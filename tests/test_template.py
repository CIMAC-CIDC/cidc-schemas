# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template` module."""

import os
import pytest

from cidc_schemas.template import Template

# NOTE: see conftest.py for pbmc_template and tiny_template fixture definitions


def test_pbmc_loaded(pbmc_template):
    """Smoke test to ensure worksheets loaded from pbmc template"""
    assert 'PBMCs' in pbmc_template.worksheets


def test_tiny_loaded(tiny_template):
    """Smoke test to ensure worksheets loaded from tiny template"""
    assert 'TEST_SHEET' in tiny_template.worksheets


def test_worksheet_validation():
    """Check validation errors on invalid worksheets"""

    def check_validation_error(schema, msg):
        with pytest.raises(AssertionError) as e:
            Template._validate_worksheet("", schema)
        assert msg in str(e.value)

    unknown_section = {
        'title': '',
        'properties': {
            'unknown_section_name': []
        }
    }
    check_validation_error(unknown_section, 'unknown worksheet sections')

    # TODO: do we need any other worksheet-level validations?


def test_worksheet_processing():
    """Ensure that worksheet schemas are processed as expected"""
    worksheet = {
        "preamble_rows": {
            # should be converted to lowercase
            "aAa": {}
        },
        "data_columns": {
            # shouldn't be converted to lowercase
            "One": {
                # should be converted to lowercase
                "BbB": {}
            }
        }
    }

    target = {
        "preamble_rows": {
            "aaa": {}
        },
        "data_columns": {
            "One": {
                "bbb": {}
            }
        }
    }

    assert Template._process_worksheet(worksheet) == target
