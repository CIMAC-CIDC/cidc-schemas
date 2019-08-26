# -*- coding: utf-8 -*-

"""The underlying data representation of an assay or shipping manifest template."""

import logging
import uuid
import json
import jsonschema
from typing import List, Optional, Dict, BinaryIO, Union
from collections import OrderedDict

from .constants import SCHEMA_DIR
from .json_validation import load_and_validate_schema

logger = logging.getLogger('cidc_schemas.template')


class Template:
    """
    Configuration describing a manifest or assay template

    Properties:
        template_schema {dict} -- a validated template JSON schema
        worksheets {Dict[str, dict]} -- a mapping from worksheet names to worksheet schemas
    """

    def __init__(self, template_schema: dict, name = None):
        """
        Load the schema defining a manifest or assay template.

        Arguments:
            template_schema {dict} -- a valid JSON schema describing a template
            name -- a "name" for repr
        """
        self.template_schema = template_schema
        self._name = name
        self.worksheets = self._extract_worksheets()
        self.key_lu = self._load_keylookup()

    def __repr__(self):
        return f"<Template({self._name if self._name else self.template_schema})>"

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


    @staticmethod
    def _get_ref_coerce(ref: str):
        """
        This function takes a json-schema style $ref pointer,
        opens the schema and determines the best python
        function to type the value.

        Args:
            ref: /path/to/schema.json

        Returns:
            Python function pointer
        """

        referer = {'$ref': ref}

        resolver_cache = {}
        while '$ref' in referer:
            # get the entry
            resolver = jsonschema.RefResolver(
                f'file://{SCHEMA_DIR}/schemas', referer, resolver_cache)
            _, referer = resolver.resolve(referer['$ref'])

        entry = referer
        # add our own type conversion
        t = entry['type']

        return Template._get_coerce(t, entry.get("$id"))

    @staticmethod
    def _get_coerce(t: str, object_id = None):
        """
        This function takes a json-schema style type
        and determines the best python
        function to type the value.
        """

        if t == 'string':
            return str
        elif t == 'integer':
            return int
        elif t == 'number':
            return float
        elif t == 'boolean':
            return bool

        # if it's an artifact that will be loaded through local file
        # we just return uuid as value 
        elif t == 'object' and object_id == "local_file":
            return lambda _: str(uuid.uuid4())
        else:
            raise NotImplementedError(f"no coercion available for type:{t}")


    def _load_keylookup(self) -> dict:
        """
        The excel spreadsheet uses human friendly (no _) names
        for properties, where the field it refers to in the schema
        has a different name. This function builds a dictionary
        to lookup these.

        It also populates the coercion function for each
        property.

        Returns:
            Dictionary keyed by spreadsheet property names
        """

        # create a key lookup dictionary
        key_lu = {}

        def _add_coerce(field_def:dict) -> dict: 
            # checks if we have a cast func for that 'type_ref'
            if 'type' in field_def:
                coerce = self._get_coerce(field_def['type'])
            else:
                coerce = self._get_ref_coerce(field_def.get('type_ref') or field_def['$ref'])

            return dict(coerce=coerce, **field_def)

        # loop over each worksheet
        for ws_name, ws_schema in self.worksheets.items():

            # loop over each row in pre-amble
            for preamble_key, preamble_def in ws_schema.get('preamble_rows', {}).items():

                # populate lookup
                key_lu[preamble_key] = _add_coerce(preamble_def)
                # we expect preamble_def from `_template.json` have 2 fields
                # (as for template.schema) - "merge_pointer" and "type_ref"

            # load the data columns
            for section_key, section_def in ws_schema.get('data_columns', {}).items():                
                for column_key, column_def in section_def.items():

                    # populate lookup
                    key_lu[column_key] = _add_coerce(column_def)
                    # we expect column_def from `_template.json` have 2 fields
                    # (as for template.schema) - "merge_pointer" and "type_ref"

        return key_lu




    # XlTemplateReader only knows how to format these types of sections
    VALID_WS_SECTIONS = set(['preamble_rows',
        'data_columns',
        'prism_preamble_object_pointer',
        'prism_data_object_pointer',
        'prism_preamble_object_schema'])

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

        return Template(template_schema, name=template_schema_path)

    def to_excel(self, xlsx_path: str):
        """Write this `Template` to an Excel file"""
        from .template_writer import XlTemplateWriter

        XlTemplateWriter().write(xlsx_path, self)

    def validate_excel(self, xlsx: Union[str, BinaryIO], raise_validation_errors: bool = True) -> bool:
        """Validate the given Excel file (either a path or an open file) against this `Template`"""
        from .template_reader import XlTemplateReader

        return XlTemplateReader.from_excel(xlsx).validate(self, raise_validation_errors)