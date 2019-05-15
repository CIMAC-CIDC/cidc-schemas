# -*- coding: utf-8 -*-

"""The underlying data representation of a shipping manifest template."""

import logging
import json
from typing import List, Optional, Dict
from collections import OrderedDict

import jsonref

from .json_validation import load_and_validate_schema

logger = logging.getLogger('cidc_schemas.manifest')


class ShippingManifest:
    """
    Configuration describing a manifest template

    Properties:
        manifest {dict} -- a validated manifest JSON schema
        worksheets {Dict[str, dict]} -- a mapping from worksheet names to worksheet schemas
    """

    def __init__(self, manifest: dict):
        """
        Load all schemas defining a shipping manifest template.

        Arguments:
            manifest {dict} -- a valid JSON schema describing a manifest
        """
        self.manifest = manifest
        self.worksheets = self._extract_worksheets()

    def _extract_worksheets(self) -> Dict[str, dict]:
        """Build a mapping from worksheet names to worksheet section schemas"""

        manifest_id = self.manifest['$id']
        assert 'worksheets' in self.manifest[
            'properties'], f'{manifest_id} schema missing "worksheets" property'
        worksheet_schemas = self.manifest['properties']['worksheets']

        assert 'items' in worksheet_schemas, f'{manifest_id}#worksheets schema missing "items" property'

        worksheets = {}
        for worksheet in worksheet_schemas['items']:
            self._validate_worksheet(worksheet)
            worksheets[worksheet['title']] = worksheet['properties']

        return worksheets

    VALID_WS_SECTIONS = set(['preamble_rows', 'data_columns'])

    @staticmethod
    def _validate_worksheet(ws_schema: dict):
        assert 'title' in ws_schema, 'found worksheet schema missing "title" property'

        ws_title = ws_schema['title']
        assert 'properties' in ws_schema, f'worksheet {ws_title} missing "properties" property'

        # Ensure all worksheet sections are supported
        ws_sections = set(ws_schema['properties'].keys())
        unknown_props = ws_sections.difference(
            ShippingManifest.VALID_WS_SECTIONS)
        assert not unknown_props, \
            f'unknown worksheet sections {unknown_props} - only {ShippingManifest.VALID_WS_SECTIONS} supported'

    @staticmethod
    def from_json(manifest_schema_path: str, schema_root: str):
        """
        Load a ShippingManifest from a manifest schema.

        Arguments:
            manifest_schema_path {str} -- path to the manifest schema file
            schema_root {str} -- path to the directory where all schemas are stored
        """
        manifest = load_and_validate_schema(
            manifest_schema_path, schema_root)

        return ShippingManifest(manifest)

    def to_excel(self, xlsx_path: str):
        """Write this `ShippingManifest` to an Excel file"""
        from .template_writer import XlTemplateWriter

        XlTemplateWriter().write(xlsx_path, self)

    def validate_excel(self, xlsx_path: str) -> bool:
        """Validate the given Excel file against this `ShippingManifest`"""
        from .template_reader import XlTemplateReader

        return XlTemplateReader.from_excel(xlsx_path).validate(self)
