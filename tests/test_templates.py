#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for template/assay template schemas."""

import os
import pytest

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template, _TEMPLATE_PATH_MAP
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader, ValidationError

from .constants import ROOT_DIR, TEMPLATE_EXAMPLES_DIR


def template_set():
    """
    Get the path to every template schema in the schemas/templates directory
    and their corresponding xlsx example file. 
    """
    # Collect template xlsx examples
    for templ_type in _TEMPLATE_PATH_MAP:
        xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, f'{templ_type}_template.xlsx')
        templ = Template.from_type(templ_type)
        yield (templ, xlsx_path)


@pytest.mark.parametrize('template, xlsx_path', template_set())
def test_template(template, xlsx_path, tmpdir):
    """
    Ensure the template schema generates a spreadsheet that looks like the given example,
    and check that the template example is valid.
    """

    # write template to a temporary file
    p = tmpdir.join('test_output.xlsx')
    template.to_excel(p)
    generated_template, err = XlTemplateReader.from_excel(p)
    assert not err

    # Ensure the xlsx file actually exists
    assert os.path.exists(
        xlsx_path), f'No example Excel template provided for {template.type}'
    reference_template, err = XlTemplateReader.from_excel(xlsx_path)
    assert not err

    # Check that both templates have the same fields
    compare_templates(template.type, generated_template, reference_template)

    # Validate the Excel template
    assert reference_template.validate(template)

    # Ensure the example Excel template isn't valid as any other template
    for other_template, _ in template_set():
        if other_template.type == template.type:
            continue
        with pytest.raises(ValidationError):
            other_template.validate_excel(xlsx_path)


def compare_templates(template_name: str, generated: XlTemplateReader, reference: XlTemplateReader):
    """Compare a generated template to a reference template."""

    worksheet_names = reference.grouped_rows.keys()

    def error(msg):
        return f'{template_name}: {msg}'

    for name in worksheet_names:
        assert name in generated.grouped_rows, error(
            f'missing worksheet {name} in generated template')
        gen_ws = generated.grouped_rows[name]
        ref_ws = reference.grouped_rows[name]

        # Compare preamble rows
        for (gen_row, ref_row) in zip(gen_ws[RowType.PREAMBLE], ref_ws[RowType.PREAMBLE]):
            gen_key, ref_key = gen_row.values[0], ref_row.values[0]
            assert gen_key.lower() == ref_key.lower(), error(
                f'preamble: generated template had key {gen_key} where reference had {ref_key}')

        assert len(gen_ws[RowType.HEADER]) == len(ref_ws[RowType.HEADER])
        for gen_headers, ref_headers in zip(gen_ws[RowType.HEADER], ref_ws[RowType.HEADER]):
            # Compare data headers
            for (gen_h, ref_h) in zip(gen_headers.values, ref_headers.values):
                assert (gen_h and gen_h.lower()) == (ref_h and ref_h.lower()), error(
                    f'data: generated template had header {gen_h!r} where reference had {ref_h!r}')
