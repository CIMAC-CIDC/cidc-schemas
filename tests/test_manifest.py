# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.manifest` module."""

import os
import pytest

from cidc_schemas.manifest import ShippingManifest

# NOTE: see conftest.py for pbmc_manifest and tiny_manifest fixture definitions


def test_pbmc_loaded(pbmc_manifest):
    """Smoke test to ensure worksheets loaded from pbmc template"""
    assert 'CORE_DATA' in pbmc_manifest.worksheets


def test_tiny_loaded(tiny_manifest):
    """Smoke test to ensure worksheets loaded from tiny template"""
    assert 'TEST_SHEET' in tiny_manifest.worksheets


def test_worksheet_validation():
    """Check validation errors on invalid worksheets"""

    def check_validation_error(schema, msg):
        with pytest.raises(AssertionError) as e:
            ShippingManifest._validate_worksheet("", schema)
        assert msg in str(e.value)

    unknown_section = {
        'title': '',
        'properties': {
            'unknown_section_name': []
        }
    }
    check_validation_error(unknown_section, 'unknown worksheet sections')

    # TODO: do we need any other worksheet-level validations?
