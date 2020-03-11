# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template_writer` module."""

from cidc_schemas.template_writer import XlTemplateWriter, RowType, row_type_from_string


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


def test_get_data_dict_mapping():
    """Test validation information extraction for template fields"""

    res = XlTemplateWriter._get_data_dict_mapping(10, 1, "data_dict_worksheet_name")
    assert res == "'data_dict_worksheet_name'!B2:B11"  # 10 rows of the second column

    res = XlTemplateWriter._get_data_dict_mapping(2, 10, "data_dict_worksheet_name")
    assert res == "'data_dict_worksheet_name'!K2:K3"  # 2 rows of the 10th column


def test_row_type_from_string():
    """Test RowType extraction from parsed strings"""

    assert row_type_from_string("#t") == RowType.TITLE
    assert row_type_from_string("t") == None
    assert row_type_from_string("") == None
