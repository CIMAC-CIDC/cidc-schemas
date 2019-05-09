# -*- coding: utf-8 -*-

"""The underlying data representation of a shipping manifest template."""

import logging
import json
from datetime import date, time
from typing import Tuple, List, Dict, Optional
from enum import Enum
from itertools import chain
from collections import OrderedDict

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

logger = logging.getLogger('cidc_schemas.manifest')


class RowType(Enum):
    """Annotations denoting what type of data a template row contains."""
    TITLE = "#t"
    HEADER = "#h"
    PREAMBLE = "#p"
    DATA = "#d"


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
        XlTemplateWriter(xlsx_path, self).write()


class XlTemplateWriter:
    """A wrapper around xlsxwriter that can create templates for shipping manifests"""

    # Output config
    DATA_ROWS = 200
    COLUMN_WIDTH_PX = 30

    def __init__(self, outfile_path: str, manifest: ShippingManifest):
        """
        Initialize an Excel template writer. No file is written until
        `write()` is called.

        Arguments:
            outfile_path {str} -- desired output path of the resulting xlsx file
            manifest {ShippingManifest} -- the manifest from which to generate a template
        """
        self.path = outfile_path
        self.workbook = xlsxwriter.Workbook(outfile_path)
        self.mainsheet = self.workbook.add_worksheet()
        self.MAIN_WIDTH = len(manifest.shipping_schemas) + \
            len(manifest.receiving_schemas)

        self.mainsheet.set_column(1, 100, width=self.COLUMN_WIDTH_PX)

        self.manifest = manifest
        self.row = 0
        self.col = 1
        self.already_written = False

        self._init_themes()

    def write(self):
        """Generate the Excel file according to the instance's configuration."""
        if self.already_written:
            logger.warning(
                f'template already written to {self.path} - aborting write')
            return

        self._write_title(self.manifest.manifest['title'])
        self.row += 1

        for entity in self.manifest.preamble_schemas.items():
            self._write_preamble_row(entity)
            self.row += 1

        # Leave a blank row between preamble and data sections
        self.row += 1

        self._write_shipping_receiving_directive()
        self.row += 1

        self._write_data_section_type_annotations()

        all_data_columns = chain(self.manifest.shipping_schemas.items(
        ), self.manifest.receiving_schemas.items())
        for entity in all_data_columns:
            self._write_data_column(entity)
            self.col += 1

        self._hide_type_annotations()
        self.workbook.close()
        self.already_written = True

    # We can think of the below _write_* functions as "template components".
    # Template components write to the spreadsheet at the current row/column
    # location, but *should not* update that location -- only the write orchestration function (above)
    # should make updates to the current row/column location.
    #
    # So, adding a section to the spreadsheet should involve:
    #  1) Adding a template component function below.
    #  2) Calling that template component in the appropriate spot in the write orchestrator.

    def _write_title(self, title: str):
        self._write_type_annotation(RowType.TITLE)
        preamble_range = xl_range(
            self.row, 1, self.row, self.MAIN_WIDTH)
        self.mainsheet.merge_range(
            preamble_range, title.upper(), self.TITLE_THEME)

    def _write_preamble_row(self, entity: Tuple[str, dict]):
        entity_name, entity_schema = entity

        # Write row type and entity name
        self._write_type_annotation(RowType.PREAMBLE)
        self.mainsheet.write(
            self.row, 1, entity_name.upper(), self.PREAMBLE_THEME)
        self._write_comment(self.row, 1, entity_schema)

        # Format value cells
        blank_row = [""] * (self.MAIN_WIDTH - 1)
        self.mainsheet.write_row(self.row, 2, blank_row, self.PREAMBLE_THEME)

        # Add data validation if appropriate
        value_cell = xl_rowcol_to_cell(self.row, 2)
        self._write_validation(value_cell, entity_schema)

    def _write_shipping_receiving_directive(self):
        shipping_width = len(self.manifest.shipping_schemas)
        receiving_width = len(self.manifest.receiving_schemas)
        self.mainsheet.merge_range(self.row, 1, self.row, shipping_width,
                                   'Filled by Biorepository', self.DIRECTIVE_THEME)
        self.mainsheet.merge_range(self.row, shipping_width + 1, self.row,
                                   receiving_width + shipping_width, 'Filled by CIMAC Lab', self.DIRECTIVE_THEME)

    def _write_type_annotation(self, row_type: RowType):
        """
        Writes a `RowType` to the first column in the current row.

        These annotations are intended to help with parsing spreadsheets.
        """
        self.mainsheet.write(self.row, 0, row_type.value)

    def _write_data_section_type_annotations(self):
        self._write_type_annotation(RowType.HEADER)
        annotations = [RowType.DATA.value] * self.DATA_ROWS
        self.mainsheet.write_column(self.row + 1, 0, annotations)

    def _write_data_column(self, entity: Tuple[str, dict]):
        entity_name, entity_schema = entity
        self.mainsheet.write(self.row, self.col,
                             entity_name.upper(), self.HEADER_THEME)
        self._write_comment(self.row, self.col, entity_schema)

        # Write validation to data cells below header cell
        data_range = xl_range(self.row + 1, self.col,
                              self.row + self.DATA_ROWS, self.col)
        self._write_validation(data_range, entity_schema)

    def _write_comment(self, row: int, col: int, entity_schema: dict):
        if 'description' in entity_schema:
            self.mainsheet.write_comment(
                row, col, entity_schema['description'], self.COMMENT_THEME)

    def _write_validation(self, cell: str, entity_schema: dict):
        validation = self._get_validation(cell, entity_schema)
        validation and self.mainsheet.data_validation(cell, validation)

    def _hide_type_annotations(self):
        self.mainsheet.set_column(0, 0, None, None, {'hidden': True})

    @staticmethod
    def _get_validation(cell: str, property_schema: dict) -> Optional[dict]:
        property_enum = property_schema.get('enum')
        property_format = property_schema.get('format')
        if property_enum and len(property_enum) > 0:
            return {'validate': 'list', 'source': property_enum}
        elif property_format == 'date':
            return {
                'validate': 'custom',
                'value': XlTemplateWriter._make_date_validation_string(cell),
                'error_message': 'Please enter date in format mm/dd/yyyy'
            }
        elif property_format == 'time':
            return {
                'validate': 'time',
                'criteria': 'between',
                'minimum': time(0, 0),
                'maximum': time(23, 59),
                'error_message': 'Please enter time in format hh:mm'
            }
        return None

    @staticmethod
    def _make_date_validation_string(cell: str) -> str:
        return f'=AND(ISNUMBER({cell}),LEFT(CELL("format",{cell}),1)="D")'

    def _init_themes(self):
        self.TITLE_THEME = self.workbook.add_format({
            'border': 1,
            'bg_color': '#ffffb3',
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'indent': 1,
        })
        self.PREAMBLE_THEME = self.workbook.add_format({
            'border': 0,
            'top': 2,
            'top_color': 'white',
            'bottom': 2,
            'bottom_color': 'white',
            'bg_color': '#b2d2f6',
            'bold': True,
            'align': 'right',
            'text_wrap': True,
            'valign': 'vcenter',
            'indent': 1,
        })
        self.HEADER_THEME = self.workbook.add_format({
            'border': 1,
            'bg_color': '#C6EFCE',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'indent': 1,
        })
        self.DATA_THEME = self.workbook.add_format({
            'border': 1,
            'bg_color': '#5fa3f0',
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'indent': 1,
        })
        self.DIRECTIVE_THEME = self.workbook.add_format({
            'border': 1,
            'bg_color': '#ffffb3',
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'indent': 1,
        })
        self.COMMENT_THEME = {
            'color': 'white',
            'font_size': 10,
            'x_scale': 2,
            'author': 'CIDC'
        }
