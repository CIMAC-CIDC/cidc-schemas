# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.manifest` module."""

import os
import pytest
from cidc_schemas.manifest import ShippingManifest


@pytest.fixture
def manifest():
    ROOT_DIR = os.path.abspath('.')
    SCHEMA_DIR = os.path.abspath(os.path.join(ROOT_DIR, 'schemas'))

    manifest_path = os.path.join(ROOT_DIR, 'manifests', 'pbmc.json')
    schema_paths = [os.path.join(SCHEMA_DIR, path)
                    for path in os.listdir(SCHEMA_DIR)]

    return ShippingManifest.from_json(manifest_path, schema_paths)


def test_manifest_loaded(manifest):
    assert manifest.manifest['id'] == 'pbmc_shipping'


def test_preamble_loaded(manifest):
    date_shipped = manifest.preamble_schemas.get('date_shipped')
    assert date_shipped is not None
    assert date_shipped['format'] == 'date'


def test_shipping_loaded(manifest):
    specimen_type = manifest.shipping_schemas.get('specimen_type')
    assert specimen_type is not None
    assert specimen_type['enum'] is not None


@pytest.fixture
def tiny_manifest():
    fake_manifest = {'test_columns': ['test_entity.test_property']}
    fake_schemas = {'test_entity':  {
        'properties': {'test_property': 'success'}}}
    return ShippingManifest(fake_manifest, fake_schemas)


def test_extract_entity_schema(tiny_manifest):
    assert tiny_manifest._extract_entity_schema(
        'test_entity', 'test_property') == 'success'


def test_extract_section_schemas(tiny_manifest):
    assert 'test_property' in tiny_manifest._extract_section_schemas(
        'test_columns')
