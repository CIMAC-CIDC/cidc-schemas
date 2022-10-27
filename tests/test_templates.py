#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for template/assay template schemas."""

import os
import pytest
import openpyxl

from cidc_schemas.template import Template, _TEMPLATE_PATH_MAP
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader, ValidationError
from cidc_schemas.template_writer import XlTemplateWriter

from .constants import TEMPLATE_EXAMPLES_DIR


def template_set():
    """
    Get the path to every template schema in the schemas/templates directory
    and their corresponding xlsx example file.
    """
    # Collect template xlsx examples
    for templ_type in _TEMPLATE_PATH_MAP:
        xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, f"{templ_type}_template.xlsx")
        templ = Template.from_type(templ_type)
        yield (templ, xlsx_path)


@pytest.fixture(scope="session", params=_TEMPLATE_PATH_MAP.keys())
def template(request):
    return Template.from_type(request.param)


@pytest.fixture(scope="session")
def template_example_xlsx_path(template):
    return os.path.join(TEMPLATE_EXAMPLES_DIR, f"{template.type}_template.xlsx")


@pytest.fixture(scope="session")
def template_example(template, template_example_xlsx_path):
    # Ensure the xlsx file actually exists
    assert os.path.exists(
        template_example_xlsx_path
    ), f"No example Excel template provided for {template.type}"
    reference, err = XlTemplateReader.from_excel(template_example_xlsx_path)
    assert not err
    return reference


def test_template(template, template_example, template_example_xlsx_path, tmpdir):
    """
    Ensure the template schema generates a spreadsheet that looks like the given example,
    and check that the template example is valid.
    """

    # write template to a temporary file
    p = tmpdir.join("test_output.xlsx")
    template.to_excel(p)
    generated_template, err = XlTemplateReader.from_excel(p)
    assert not err

    reference_template = template_example

    # Check that both templates have the same fields
    compare_templates(template.type, generated_template, reference_template)

    # Validate the Excel template
    assert reference_template.validate(template)

    # Ensure the example Excel template isn't valid as any other template
    for other_template_type in _TEMPLATE_PATH_MAP:
        if other_template_type == template.type:
            # don't check it against itself
            continue

        other_template = Template.from_type(other_template_type)
        with pytest.raises(ValidationError):
            other_template.validate_excel(template_example_xlsx_path)

    # Ensure that the data dictionary tab in this template doesn't have empty columns
    generated_xlsx = openpyxl.load_workbook(p)
    data_dict_ws = generated_xlsx[XlTemplateWriter._data_dict_sheet_name]
    for col in data_dict_ws.iter_cols(
        min_col=2, max_col=50, max_row=10, values_only=True
    ):
        [header, *values] = col
        if header is None:
            break
        assert any(val is not None for val in values)


def compare_templates(
    template_name: str, generated: XlTemplateReader, reference: XlTemplateReader
):
    """Compare a generated template to a reference template."""

    worksheet_names = reference.grouped_rows.keys()

    def error(msg):
        return f"{template_name}: {msg}"

    for name in worksheet_names:
        assert name in generated.grouped_rows, error(
            f"missing worksheet {name} in generated template"
        )
        gen_ws = generated.grouped_rows[name]
        ref_ws = reference.grouped_rows[name]

        # Compare preamble rows
        for (gen_row, ref_row) in zip(
            gen_ws[RowType.PREAMBLE], ref_ws[RowType.PREAMBLE]
        ):
            gen_key, ref_key = gen_row.values[0], ref_row.values[0]
            assert gen_key.lower() == ref_key.lower(), error(
                f"preamble: generated template had key {gen_key} where reference had {ref_key}"
            )

        assert len(gen_ws[RowType.HEADER]) == len(ref_ws[RowType.HEADER])
        for gen_headers, ref_headers in zip(
            gen_ws[RowType.HEADER], ref_ws[RowType.HEADER]
        ):
            # Compare data headers
            for (gen_h, ref_h) in zip(gen_headers.values, ref_headers.values):
                assert (gen_h and gen_h.lower()) == (ref_h and ref_h.lower()), error(
                    f"data: generated template had header {gen_h!r} where reference had {ref_h!r}"
                )
