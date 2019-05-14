# -*- coding: utf-8 -*-

"""Global test configuration and shared fixtures"""

import os

import pytest

from cidc_schemas.manifest import ShippingManifest


@pytest.fixture
def pbmc_manifest(schema_paths, manifest_dir):
    pbmc_manifest_path = os.path.join(manifest_dir, 'pbmc', 'pbmc.json')
    return ShippingManifest.from_json(pbmc_manifest_path, schema_paths)


@pytest.fixture
def tiny_manifest():
    fake_manifest = {'test_columns': [
        'test_entity.test_property',
        'test_entity.test_date',
        'test_entity.test_time'
    ]}
    fake_schemas = {
        'test_entity':  {
            'properties': {
                'test_property': {'$id': 'success', 'type': 'string'},
                'test_date': {'type': 'string', 'format': 'date'},
                'test_time': {'type': 'string', 'format': 'time'}
            }
        }
    }
    return ShippingManifest(fake_manifest, fake_schemas)
