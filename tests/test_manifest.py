# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.manifest` module."""

import os
import pytest

from cidc_schemas.manifest import ShippingManifest

# NOTE: see conftest.py for pbmc_manifest and tiny_manifest fixture definitions


def test_pbmc_loaded(pbmc_manifest):
    assert 'CORE_DATA' in pbmc_manifest.worksheets


def test_tiny_loaded(tiny_manifest):
    assert 'FAKE_SHEET' in tiny_manifest.worksheets


def test_worksheet_schema_validation():
    def check_validation_error(schema, msg):
        with pytest.raises(AssertionError) as e:
            ShippingManifest._validate_worksheet(schema)
        assert msg in str(e.value)

    no_title = {}
    check_validation_error(no_title, 'missing "title"')

    no_properties = {
        'title': ''
    }
    check_validation_error(no_properties, 'missing "properties"')

    unknown_section = {
        'title': '',
        'properties': {
            'unknown_section_name': []
        }
    }
    check_validation_error(unknown_section, 'unknown worksheet sections')
