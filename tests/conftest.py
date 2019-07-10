# -*- coding: utf-8 -*-

"""Global test configuration and shared fixtures"""

import os

import pytest

from cidc_schemas.template import Template

from .constants import SCHEMA_DIR


@pytest.fixture
def pbmc_template():
    pbmc_template_path = os.path.join(SCHEMA_DIR, 'templates', 'pbmc_template.json')
    return Template.from_json(pbmc_template_path, SCHEMA_DIR)


@pytest.fixture
def tiny_template():
    """A small, valid """

    test_property = {'$id': 'success', 'type': 'string'}
    test_date = {'type': 'string', 'format': 'date'}
    test_time = {'type': 'string', 'format': 'time'}
    test_fields = {
        'test_property': test_property,
        'test_date': test_date,
        'test_time': test_time
    }

    tiny_template_schema = {
        '$id': 'tiny_template',
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

    return Template(tiny_template_schema)
