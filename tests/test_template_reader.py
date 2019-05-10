#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_template_reader.template_reader` module."""

import os
import pytest
import jsonschema
from typing import List
from openpyxl import load_workbook

from cidc_schemas import template_reader
from cidc_schemas.template_writer import RowType


def test_valid_tiny_validation(tiny_manifest):
    tiny_valid = [
        (RowType.PREAMBLE, 'test_property', 'foo'),
        (RowType.PREAMBLE, 'test_date', '6/11/12'),
        (RowType.PREAMBLE, 'test_time', '10:44:61'),
        (RowType.HEADER, 'test_property', 'test_date', 'test_time'),
        (RowType.DATA, 'foo', '6/11/12', '10:44:61'),
        (RowType.DATA, 'foo', '6/12/12', '10:45:61')
    ]

    reader = template_reader.XlTemplateReader(tiny_valid)
    assert reader.validate(tiny_manifest)


def test_invalid_tiny_validation(tiny_manifest):
    tiny_invalid = [
        (RowType.PREAMBLE, 'test_property', 'foo'),
        (RowType.PREAMBLE, 'test_date', '6foo'),
        (RowType.PREAMBLE, 'test_time', '10:foo:61'),
        (RowType.HEADER, 'test_property', 'test_date', 'test_time'),
        (RowType.DATA, 'foo', '6/11/foo', '10::::44:61'),
        (RowType.DATA, 'foo', '6//12', '10:45:61asdf')
    ]

    reader = template_reader.XlTemplateReader(tiny_invalid)
    assert not reader.validate(tiny_manifest)
