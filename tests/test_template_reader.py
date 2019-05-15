#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_template_reader.template_reader` module."""

import os
import pytest
import jsonschema
from typing import List
from openpyxl import load_workbook

from cidc_schemas.template_reader import XlTemplateReader, ValidationError
from cidc_schemas.template_writer import RowType

from .constants import MANIFEST_EXAMPLES_DIR, TEST_DATA_DIR

# NOTE: see conftest.py for pbmc_manifest and tiny_manifest fixture definitions


def test_valid_tiny_validation(tiny_manifest):
    tiny_valid = {
        'FAKE_SHEET': [
            (RowType.PREAMBLE, 'test_property', 'foo'),
            (RowType.PREAMBLE, 'test_date', '6/11/12'),
            (RowType.PREAMBLE, 'test_time', '10:44:61'),
            (RowType.HEADER, 'test_property', 'test_date', 'test_time'),
            (RowType.DATA, 'foo', '6/11/12', '10:44:61'),
            (RowType.DATA, 'foo', '6/12/12', '10:45:61')
        ]
    }

    reader = XlTemplateReader(tiny_valid)
    assert reader.validate(tiny_manifest)


def test_invalid_tiny_preamble(tiny_manifest):
    tiny_invalid = {
        'FAKE_SHEET': [
            (RowType.PREAMBLE, 'test_property', 'foo'),
            (RowType.PREAMBLE, 'test_date', '6foo'),
            (RowType.PREAMBLE, 'test_time', '10:foo:61'),
            (RowType.HEADER, 'test_property', 'test_date', 'test_time'),
            (RowType.DATA, 'foo', '6/11/foo', '10::::44:61'),
            (RowType.DATA, 'foo', '6//12', '10:45:61asdf')
        ]
    }

    reader = XlTemplateReader(tiny_invalid)

    with pytest.raises(ValidationError) as e:
        reader.validate(tiny_manifest)


def test_pbmc_validation(pbmc_manifest):
    pbmc_xlsx_path = os.path.join(MANIFEST_EXAMPLES_DIR, 'pbmc.xlsx')
    assert pbmc_manifest.validate_excel(pbmc_xlsx_path)


def test_pbmc_invalidation(pbmc_manifest):
    pbmc_xlsx_path = os.path.join(TEST_DATA_DIR, 'pbmc_invalid.xlsx')
    with pytest.raises(ValidationError):
        pbmc_manifest.validate_excel(pbmc_xlsx_path)
