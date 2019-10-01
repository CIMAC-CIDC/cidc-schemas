#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_template_reader.template_reader` module."""

import os
import pytest
import jsonschema
from typing import List
from openpyxl import load_workbook

from cidc_schemas.template_reader import XlTemplateReader, ValidationError, TemplateRow
from cidc_schemas.template_writer import RowType

from .constants import TEMPLATE_EXAMPLES_DIR, TEST_DATA_DIR

# NOTE: see conftest.py for pbmc_template and tiny_template fixture definitions


def test_valid(tiny_template):
    """Test that a known-valid spreadsheet is considered valid"""
    tiny_valid = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.PREAMBLE, ('test_property', 'foo')),
            TemplateRow(2, RowType.PREAMBLE, ('test_date', '6/11/12')),
            TemplateRow(3, RowType.PREAMBLE, ('test_time', '10:44:61')),
            TemplateRow(4, RowType.HEADER, ('test_property',
                                            'test_date', 'test_time')),
            TemplateRow(5, RowType.DATA, ('foo', '6/11/12', '10:44:61')),
            TemplateRow(6, RowType.DATA, ('foo', '6/12/12', '10:45:61'))
        ]
    }

    reader = XlTemplateReader(tiny_valid)
    assert reader.validate(tiny_template)


def test_valid_from_excel(tiny_template):
    """Test that the reader can load from a small xlsx file"""
    tiny_xlsx = os.path.join(TEST_DATA_DIR, 'tiny_manifest.xlsx')
    reader = XlTemplateReader.from_excel(tiny_xlsx)
    assert reader.validate(tiny_template)


def search_error_message(workbook, template, error, msg_fragment):
    reader = XlTemplateReader(workbook)
    with pytest.raises(error, match=msg_fragment):
        reader.validate(template)


def test_empty_headers(tiny_template):
    """Test that a spreadsheet with empty headers raises a validation error"""
    tiny_missing_header = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.HEADER,
                        ('test_property', None, 'test_time')),
        ]
    }

    search_error_message(tiny_missing_header, tiny_template,
                         ValidationError, 'empty header cell')


def test_missing_rows_or_columns(tiny_template):
    """Test that a template with missing rows or columns raises a validation error"""
    missing_rows_and_columns = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.PREAMBLE, ('test_property', 'foo')),
            TemplateRow(2, RowType.PREAMBLE, ('test_date', '6/11/12')),
            TemplateRow(3, RowType.HEADER,
                        ('test_property', 'test_time')),
        ]
    }

    search_error_message(missing_rows_and_columns, tiny_template,
                         ValidationError, "expected template row: 'test_time")

    search_error_message(missing_rows_and_columns, tiny_template,
                         ValidationError, "expected template column: 'test_date")


def test_missing_required_value(tiny_template):
    """Test that spreadsheet with a missing value marked required raises a validation error"""
    tiny_missing_value = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.HEADER, ('test_property',
                                            'test_date', 'test_time')),
            TemplateRow(2, RowType.DATA, (None, '6/11/12', '10:44:61')),
        ]
    }

    message = "Error in worksheet 'TEST_SHEET', row 2, field 'test_property': found empty value"
    search_error_message(tiny_missing_value,
                         tiny_template, ValidationError, message)


def test_wrong_number_of_headers(tiny_template):
    """Test that a spreadsheet with multiple or no headers raises an validation error"""
    tiny_double = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.HEADER, ('test_property',
                                            'test_date', 'test_time')),
            TemplateRow(2, RowType.HEADER, ('test_property',
                                            'test_date', 'test_time')),
        ]
    }

    tiny_no_headers = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.DATA, (1, 2, 3))
        ]
    }

    search_error_message(tiny_double, tiny_template,
                         ValidationError, 'one header row expected')

    search_error_message(tiny_no_headers, tiny_template,
                         ValidationError, 'one header row expected')


def test_missing_schema(tiny_template):
    """Test that a spreadsheet with an unknown property raises an assertion error"""
    tiny_missing = {
        'TEST_SHEET': [
            TemplateRow(1, RowType.PREAMBLE, ('missing_property', 'foo')),
        ]
    }

    search_error_message(tiny_missing, tiny_template,
                         ValidationError, 'Found unexpected column "missing_property"')


def test_invalid(tiny_template):
    """Test that a known-invalid spreadsheet is considered invalid"""
    tiny_invalid = {
        'TEST_SHEET': [
            TemplateRow(2, RowType.PREAMBLE, ('test_property', 'foo')),
            TemplateRow(2, RowType.PREAMBLE, ('test_date', '6foo')),
            TemplateRow(2, RowType.PREAMBLE, ('test_time', '10:foo:61')),
            TemplateRow(2, RowType.HEADER, ('test_property',
                                            'test_date', 'test_time')),
            TemplateRow(2, RowType.DATA, ('foo', '6/11/foo', '10::::44:61')),
            TemplateRow(2, RowType.DATA, ('foo', '6//12', '10:45:61asdf'))
        ]
    }

    search_error_message(tiny_invalid, tiny_template,
                         ValidationError, '')


def test_pbmc_validation(pbmc_template):
    """Test that the provided pbmc shipping manifest is valid"""
    # TODO: THIS NEEDS TO BE RE-ENABLED AFTER PBMC MAJOR CHANGES ARE FIXED
    return
    pbmc_xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, 'pbmc_template.xlsx')
    assert pbmc_template.validate_excel(pbmc_xlsx_path)


def test_pbmc_invalidation(pbmc_template):
    """Test that a deliberately invalid pbmc shipping manifest is invalid"""
    # TODO: THIS NEEDS TO BE RE-ENABLED AFTER PBMC MAJOR CHANGES ARE FIXED
    return
    pbmc_xlsx_path = os.path.join(TEST_DATA_DIR, 'pbmc_invalid.xlsx')
    with pytest.raises(ValidationError):
        pbmc_template.validate_excel(pbmc_xlsx_path)
