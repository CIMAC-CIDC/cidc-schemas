# -*- coding: utf-8 -*-

"""Global test configuration and shared fixtures"""

import os

import pytest

from cidc_schemas.manifest import ShippingManifest

from .constants import SCHEMA_DIR


@pytest.fixture
def pbmc_manifest():
    pbmc_manifest_path = os.path.join(SCHEMA_DIR, 'manifests', 'pbmc.json')
    return ShippingManifest.from_json(pbmc_manifest_path, SCHEMA_DIR)


@pytest.fixture
def tiny_manifest():
    """A small, valid """

    test_property = {'$id': 'success', 'type': 'string'}
    test_date = {'type': 'string', 'format': 'date'}
    test_time = {'type': 'string', 'format': 'time'}
    test_fields = {
        'test_property': test_property,
        'test_date': test_date,
        'test_time': test_time
    }

    tiny_manifest_schema = {
        '$id': 'tiny_manifest',
        'title': 'Tiny Manifest',
        'properties': {
            'worksheets': {
                'TEST_SHEET': {
                    'preamble_rows': test_fields,
                    'data_columns': {
                        'first table': test_fields,
                        'another table': test_fields
                    }
                },
            }
        }
    }

    return ShippingManifest(tiny_manifest_schema)
