# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template_writer` module."""

from cidc_schemas.template_writer import XlTemplateWriter, RowType, row_type_from_string


def test_get_validation():
    """Test validation information extraction for template fields"""

    enum = XlTemplateWriter._get_validation("A1", {"enum": [1, 2, 3]})
    assert enum["validate"] == "list"
    assert enum["source"] == [1, 2, 3]

    time = XlTemplateWriter._get_validation("A1", {"format": "time"})
    assert time["validate"] == "time"

    date = XlTemplateWriter._get_validation("A1", {"format": "date"})
    assert date["validate"] == "custom"
    assert date["value"] == XlTemplateWriter._make_date_validation_string("A1")


def test_row_type_from_string():
    """Test RowType extraction from parsed strings"""

    assert row_type_from_string("#t") == RowType.TITLE
    assert row_type_from_string("t") == None
    assert row_type_from_string("") == None
