# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template_writer` module."""

from cidc_schemas.template_writer import (
    XlTemplateWriter,
    RowType,
    row_type_from_string,
    _format_validation_range,
)

import openpyxl


def test_get_validation():
    """Test validation information extraction for template fields"""

    enum = XlTemplateWriter._get_validation(
        "A1", "my_enum", {"enum": [1, 2, 3]}, {"my_enum": "'Data D'!whatever"}
    )
    assert enum["validate"] == "list"
    assert enum["source"] == "'Data D'!whatever"

    time = XlTemplateWriter._get_validation("A1", "my_time", {"format": "time"}, {})
    assert time["validate"] == "time"

    date = XlTemplateWriter._get_validation("A1", "my_date", {"format": "date"}, {})
    assert date["validate"] == "custom"
    assert date["value"] == XlTemplateWriter._make_date_validation_string("A1")


def test_format_validation_range():
    """Test validation information extraction for template fields"""

    res = _format_validation_range(10, 1, "data_dict_worksheet_name")
    assert (
        res == "'data_dict_worksheet_name'!$B$2:$B$11"
    )  # 10 rows of the second column

    res = _format_validation_range(2, 10, "data_dict_worksheet_name")
    assert res == "'data_dict_worksheet_name'!$K$2:$K$3"  # 2 rows of the 10th column


def test_row_type_from_string():
    """Test RowType extraction from parsed strings"""

    assert row_type_from_string("#t") == RowType.TITLE
    assert row_type_from_string("t") == None
    assert row_type_from_string("") == None


def test_enum_validation_in_template(tiny_template, tmpdir):
    """Test that the reader can load from a small xlsx file"""
    XlTemplateWriter().write(tmpdir.join("test_enum_validation.xlsx"), tiny_template)

    workbook = openpyxl.load_workbook(tmpdir.join("test_enum_validation.xlsx"))

    worksheet = workbook["TEST_SHEET"]

    for v in worksheet.data_validations.dataValidation:
        if v.type == "list":
            # checking enum in .xlsx
            assert (
                str(v.formula1)
                == f"{XlTemplateWriter._data_dict_sheet_name!r}!$D$2:$D$3"
            )
