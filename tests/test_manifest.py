# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.manifest` module."""

import os
import pytest

# NOTE: see conftest.py for pbmc_manifest and tiny_manifest fixture definitions


def test_manifest_loaded(pbmc_manifest):
    assert pbmc_manifest.manifest['id'] == 'pbmc_shipping'


def test_preamble_loaded(pbmc_manifest):
    date_shipped = pbmc_manifest.preamble_schemas.get('date_shipped')
    assert date_shipped is not None
    assert date_shipped['format'] == 'date'


def test_shipping_loaded(pbmc_manifest):
    specimen_type = pbmc_manifest.shipping_schemas.get('specimen_type')
    assert specimen_type is not None
    assert specimen_type['enum'] is not None


def test_extract_entity_schema(tiny_manifest):
    assert tiny_manifest._extract_entity_schema(
        'test_entity', 'test_property')['id'] == 'success'


def test_extract_section_schemas(tiny_manifest):
    assert 'test_property' in tiny_manifest._extract_section_schemas(
        'test_columns')
