# -*- coding: utf-8 -*-

"""The underlying data representation of a shipping manifest template."""

import logging
import json
from typing import List, Optional, Dict
from collections import OrderedDict

logger = logging.getLogger('cidc_schemas.manifest')


class ShippingManifest:
    """
    A collection of property schemas organized by their relevance to the manifest.

    Attributes:
        preamble_schemas {OrderedDict} -- entity schemas for rows in the preamble section
        shipping_schemas {OrderedDict} -- entity schemas for columns in the shipping section
        receiving_schemas {OrderedDict} -- entity schemas for columns in the receiving section
    """

    def __init__(self, manifest: Dict[str, str], schemas: Dict[str, dict]):
        """
        Load all schemas defining a shipping manifest template.

        Arguments:
            manifest {Dict[str, str]} -- a manifest configuration (keys are manifest section names, 
                                         values are selectors for schemas in that section)
            schemas {Dict[str, dict]} -- schema configurations (keys are schema ids, values are schemas)
        """
        self.manifest = manifest
        self.schemas = schemas

        # Extract schemas for manifest entities in appropriate order
        self.preamble_schemas: OrderedDict = self._extract_section_schemas(
            'core_columns')
        self.shipping_schemas: OrderedDict = self._extract_section_schemas(
            'shipping_columns')
        self.receiving_schemas: OrderedDict = self._extract_section_schemas(
            'receiving_columns')

    @staticmethod
    def from_json(manifest_path: str, schema_paths: List[str]):
        """
        Load a ShippingManifest from files containing json configuration

        Arguments:
            manifest_path {str} -- path to the manifest config json file
            schema_paths {str} -- paths to the entity schema config json files
        """
        # Load the manifest file
        with open(manifest_path, 'r') as stream:
            manifest = json.load(stream)

        #  Load all schemas for entities potentially present in manifest
        all_schemas = {}
        for schema_path in schema_paths:
            with open(schema_path, 'r') as stream:
                schema = json.load(stream)
                all_schemas[schema['id']] = schema

        return ShippingManifest(manifest, all_schemas)

    def _extract_section_schemas(self, section_name: str) -> OrderedDict:
        """Collect all entity schemas for a manifest section"""
        schemas: OrderedDict = OrderedDict()
        for path in self.manifest.get(section_name, []):
            entity, prop = path.split('.')
            maybe_schema = self._extract_entity_schema(entity, prop)
            if maybe_schema:
                schemas[prop] = maybe_schema
        return schemas

    def _extract_entity_schema(self, entity: str, prop: str) -> Optional[dict]:
        """Try to find a schema for the given entity and property"""
        entity_schema = self.schemas.get(entity)
        if not entity_schema:
            logger.warning(
                f'no top-level schema found for entity {entity} - skipping')
            return None

        prop_schema = entity_schema.get('properties', {}).get(prop)
        if not prop_schema:
            logger.warning(
                f'no property schema found for {entity}.{prop} - skipping')
            return None

        return prop_schema

    def to_excel(self, xlsx_path: str):
        """Write this `ShippingManifest` to an Excel file"""
        from .template_writer import XlTemplateWriter

        XlTemplateWriter(xlsx_path, self).write()

    def validate_excel(self, xlsx_path: str) -> bool:
        """Validate the given Excel file against this `ShippingManifest`"""
        from .template_reader import XlTemplateReader

        return XlTemplateReader.from_excel(xlsx_path).validate(self)
