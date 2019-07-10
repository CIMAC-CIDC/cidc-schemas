#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for template/assay template schemas."""

import os
import pytest

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from .constants import ROOT_DIR, SCHEMA_DIR, TEMPLATE_EXAMPLES_DIR


def template_paths():
    """
    Get the path to every template schema in the schemas/templates directory
    and their corresponding xlsx example file. 
    """
    template_schema_dir = os.path.join(SCHEMA_DIR, 'templates')

    template_paths = []

    # Collect template schemas
    for root, _, files in os.walk(template_schema_dir):
        for f in files:
            template_paths.append(os.path.join(root, f))

    # Collect template xlsx examples
    for i, schema_path in enumerate(template_paths):
        name = os.path.basename(schema_path).rsplit('.', 1)[0]
        xlsx = f'{name}.xlsx'
        xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, xlsx)
        template_paths[i] = (schema_path, xlsx_path)

    return template_paths


@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_template(schema_path, xlsx_path, tmpdir):
    """
    Ensure the template schema generates a spreadsheet that looks like the given example,
    and check that the template example is valid.
    """

    # Load the template and write it to a temporary file
    template = Template.from_json(schema_path, SCHEMA_DIR)
    p = tmpdir.join('test_output.xlsx')
    template.to_excel(p)
    generated_template = XlTemplateReader.from_excel(p)

    # Ensure the xlsx file actually exists
    assert os.path.exists(
        xlsx_path), f'No example Excel template provided for {schema_path}'
    reference_template = XlTemplateReader.from_excel(xlsx_path)

    # Check that both templates have the same fields
    compare_templates(schema_path, generated_template, reference_template)

    # Validate the Excel template
    assert reference_template.validate(template)


def compare_templates(schema_path: str, generated: XlTemplateReader, reference: XlTemplateReader):
    """Compare a generated template to a reference template."""

    worksheet_names = reference.grouped_rows.keys()

    def error(msg):
        return f'{schema_path}: {msg}'

    for name in worksheet_names:
        assert name in generated.grouped_rows, error(
            f'missing worksheet {name} in generated template')
        gen_ws = generated.grouped_rows[name]
        ref_ws = reference.grouped_rows[name]

        # Compare preamble rows
        for (gen_row, ref_row) in zip(gen_ws[RowType.PREAMBLE], ref_ws[RowType.PREAMBLE]):
            gen_key, ref_key = gen_row[0], ref_row[0]
            assert gen_key == ref_key, error(
                f'preamble: generated template had key {gen_key} where reference had {ref_key}')

        # Compare data headers
        gen_headers = gen_ws[RowType.HEADER][0]
        ref_headers = ref_ws[RowType.HEADER][0]
        for (gen_h, ref_h) in zip(gen_headers, ref_headers):
            assert gen_h == ref_h, error(
                f'data: generated template had header {gen_h} where reference had {ref_h}')
