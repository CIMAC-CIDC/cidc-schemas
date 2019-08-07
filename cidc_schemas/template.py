# -*- coding: utf-8 -*-

"""The underlying data representation of an assay or shipping manifest template."""

import os
import logging
import json
from typing import List, Optional, Dict, BinaryIO, Union
from collections import OrderedDict

from .constants import SCHEMA_DIR, TEMPLATE_DIR
from .json_validation import load_and_validate_schema

logger = logging.getLogger('cidc_schemas.template')


def generate_empty_template(schema_path: str, target_path: str):
    """Write the .xlsx template for the given schema to the target path."""
    logger.info(f"Writing empty template for {schema_path} to {target_path}.")
    template = Template.from_json(schema_path)
    template.to_excel(target_path)


def generate_all_templates(target_dir: str):
    """
    Generate empty template .xlsx files for every available template schema and 
    write them to the target directory.
    """
    # We expect two directories: one for metadata schemas and one for manifests
    for template_type_dir in os.listdir(TEMPLATE_DIR):
        # Create the directory for this template type
        target_subdir = os.path.join(target_dir, template_type_dir)
        os.makedirs(target_subdir)

        schema_subdir = os.path.join(TEMPLATE_DIR, template_type_dir)

        # Create a new empty template for each template schema in schema_subdir
        for template_schema_file in os.listdir(schema_subdir):
            schema_path = os.path.join(schema_subdir, template_schema_file)
            template_xlsx_file = template_schema_file.replace('.json', '.xlsx')
            target_path = os.path.join(target_subdir, template_xlsx_file)
            generate_empty_template(schema_path, target_path)


class Template:
    """
    Configuration describing a manifest or assay template

    Properties:
        template_schema {dict} -- a validated template JSON schema
        worksheets {Dict[str, dict]} -- a mapping from worksheet names to worksheet schemas
    """

    def __init__(self, template_schema: dict):
        """
        Load the schema defining a manifest or assay template.

        Arguments:
            template_schema {dict} -- a valid JSON schema describing a template
        """
        self.template_schema = template_schema
        self.worksheets = self._extract_worksheets()

    def _extract_worksheets(self) -> Dict[str, dict]:
        """Build a mapping from worksheet names to worksheet section schemas"""

        template_id = self.template_schema['$id']
        assert 'worksheets' in self.template_schema[
            'properties'], f'{template_id} schema missing "worksheets" property'
        worksheet_schemas = self.template_schema['properties']['worksheets']

        worksheets = {}
        for name, schema in worksheet_schemas.items():
            self._validate_worksheet(name, schema)

            worksheets[name] = self._process_worksheet(schema)

        return worksheets

    @staticmethod
    def _process_fieldname(name: str) -> str:
        """Convert field name to lowercase to ease matching"""
        return name.lower()

    @staticmethod
    def _process_worksheet(worksheet: dict) -> dict:
        """Do pre-processing on a worksheet"""

        def process_fields(schema: dict) -> dict:
            processed = {}
            for field_name, field_schema in schema.items():
                field_name_proc = Template._process_fieldname(field_name)
                processed[field_name_proc] = field_schema
            return processed

        # Process field names to ensure we can match on them later
        processed_worksheet = {}
        for section_name, section_schema in worksheet.items():
            if section_name == 'preamble_rows':
                processed_worksheet[section_name] = process_fields(
                    section_schema)
            elif section_name == 'data_columns':
                data_schemas = {}
                for table_name, table_schema in section_schema.items():
                    data_schemas[table_name] = process_fields(table_schema)
                processed_worksheet[section_name] = data_schemas

        return processed_worksheet

    # XlTemplateReader only knows how to format these types of sections
    VALID_WS_SECTIONS = set(['preamble_rows', 'data_columns'])

    @staticmethod
    def _validate_worksheet(ws_title: str, ws_schema: dict):
        # Ensure all worksheet sections are supported
        ws_sections = set(ws_schema.keys())
        unknown_props = ws_sections.difference(
            Template.VALID_WS_SECTIONS)
        assert not unknown_props, \
            f'unknown worksheet sections {unknown_props} - only {Template.VALID_WS_SECTIONS} supported'

    @staticmethod
    def from_json(template_schema_path: str, schema_root: str = SCHEMA_DIR):
        """
        Load a Template from a template schema.

        Arguments:
            template_schema_path {str} -- path to the template schema file
            schema_root {str} -- path to the directory where all schemas are stored
        """
        template_schema = load_and_validate_schema(
            template_schema_path, schema_root)

        return Template(template_schema)

    def to_excel(self, xlsx_path: str):
        """Write this `Template` to an Excel file"""
        from .template_writer import XlTemplateWriter

        XlTemplateWriter().write(xlsx_path, self)

    def validate_excel(self, xlsx: Union[str, BinaryIO], raise_validation_errors: bool = True) -> bool:
        """Validate the given Excel file (either a path or an open file) against this `Template`"""
        from .template_reader import XlTemplateReader

        return XlTemplateReader.from_excel(xlsx).validate(self, raise_validation_errors)
