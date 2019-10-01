# -*- coding: utf-8 -*-

"""Defines the `XlTemplateWriter` class for writing `Template`s to Excel templates."""

import logging
from typing import Tuple, Dict, Optional
from enum import Enum
from itertools import chain
from datetime import date, time

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

from .template import Template

logger = logging.getLogger('cidc_schemas.template_writer')


class RowType(Enum):
    """Annotations denoting what type of data a template row contains."""
    TITLE = "#t"
    HEADER = "#h"
    PREAMBLE = "#p"
    DATA = "#d"


def row_type_from_string(maybe_type: str) -> Optional[RowType]:
    try:
        return RowType(maybe_type)
    except ValueError:
        return None


class XlThemes:
    """Data class containing format specifications used in `XlTemplateWriter`"""
    TITLE_THEME = {
        'border': 1,
        'bg_color': '#ffffb3',
        'bold': True,
        'align': 'center',
        'text_wrap': True,
        'valign': 'vcenter',
        'indent': 1,
    }
    PREAMBLE_THEME = {
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
    }
    HEADER_THEME = {
        'border': 1,
        'bg_color': '#C6EFCE',
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'indent': 1,
    }
    DATA_THEME = {
        'border': 1,
        'bg_color': '#5fa3f0',
        'bold': True,
        'align': 'center',
        'text_wrap': True,
        'valign': 'vcenter',
        'indent': 1,
    }
    DIRECTIVE_THEME = {
        'border': 1,
        'bg_color': '#ffffb3',
        'bold': True,
        'align': 'center',
        'text_wrap': True,
        'valign': 'vcenter',
        'indent': 1,
    }
    COMMENT_THEME = {
        'color': 'white',
        'font_size': 10,
        'x_scale': 2,
        'author': 'CIDC'
    }


class XlTemplateWriter:
    """A wrapper around xlsxwriter that can create Excel templates from template schemas"""

    _DATA_ROWS = 200
    _MIN_NUM_COLS = 5
    _COLUMN_WIDTH_PX = 30

    def __init__(self, data_rows=_DATA_ROWS, min_num_cols=_MIN_NUM_COLS, column_width_px=_COLUMN_WIDTH_PX):
        """
        Initialize an Excel template writer.
        """
        self.DATA_ROWS = data_rows
        self.MAIN_WIDTH = min_num_cols
        self.COLUMN_WIDTH_PX = column_width_px

    def write(self, outfile_path: str, template: Template):
        """
        Generate an Excel file for the given template.

        Arguments:
            outfile_path {str} -- desired output path of the resulting xlsx file
            template {Template} -- the template configuration from which to generate an Excel file
        """
        self.path = outfile_path
        self.template = template
        self.workbook = xlsxwriter.Workbook(outfile_path)
        self._init_themes()

        first_sheet = True
        for name, ws_schema in self.template.worksheets.items():
            self._write_worksheet(
                name, ws_schema, write_title=first_sheet)
            first_sheet = False

        self.workbook.close()
        self.workbook = None

    def _write_worksheet(self, name, schema, write_title=False):
        """Write content to the given worksheet"""
        assert self.workbook, "_write_worksheet called without an initialized workbook"
        assert self.template, "_write_worksheet called without an initialized template"

        self.worksheet = self.workbook.add_worksheet(name)
        self.worksheet.set_column(1, 100, width=self.COLUMN_WIDTH_PX)

        self.row = 0
        self.col = 1

        data_columns = {}
        if 'data_columns' in schema:
            data_columns = {name: subtable
                            for name, subtable in schema['data_columns'].items()}
            num_data_columns = sum([len(columns)
                                    for columns in data_columns.values()])
            self.MAIN_WIDTH = max(self.MAIN_WIDTH, num_data_columns)

        if write_title:
            self._write_title(self.template.schema['title'])
            self.row += 1

        if 'preamble_rows' in schema:
            for name, schema in schema['preamble_rows'].items():
                self._write_preamble_row(name, schema)
                self.row += 1

            # Leave a blank row between preamble and data sections
            self.row += 1

        self._write_data_multiheaders(data_columns)
        self.row += 1

        self._write_data_section_type_annotations()

        if data_columns:
            for section_columns in data_columns.values():
                for name, schema in section_columns.items():
                    self._write_data_column(name, schema)
                    self.col += 1

        self._hide_type_annotations()

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
        self.worksheet.merge_range(
            preamble_range, title.capitalize(), self.TITLE_THEME)

    def _write_preamble_row(self, entity_name: str, entity_schema: dict):

        # Write row type and entity name
        self._write_type_annotation(RowType.PREAMBLE)
        self.worksheet.write(
            self.row, 1, entity_name.capitalize(), self.PREAMBLE_THEME)
        self._write_comment(self.row, 1, entity_schema)

        # Format value cells
        blank_row = [""] * (self.MAIN_WIDTH - 1)
        self.worksheet.write_row(
            self.row, 2, blank_row, self.PREAMBLE_THEME)

        # Add data validation if appropriate
        value_cell = xl_rowcol_to_cell(self.row, 2)
        self._write_validation(value_cell, entity_schema)

    def _write_data_multiheaders(self, data_columns: Dict[str, dict]):
        start_col = 1
        for section_header, section_values in data_columns.items():
            section_width = len(section_values)
            end_col = start_col + section_width - 1
            if end_col - start_col > 1:
                self.worksheet.merge_range(self.row, start_col, self.row, end_col,
                                           section_header, self.DIRECTIVE_THEME)
            else:
                self.worksheet.write(self.row, start_col,
                                     section_header, self.DIRECTIVE_THEME)
            start_col = end_col + 1

    def _write_type_annotation(self, row_type: RowType):
        """
        Writes a `RowType` to the first column in the current row.

        These annotations are intended to help with parsing spreadsheets.
        """
        self.worksheet.write(self.row, 0, row_type.value)

    def _write_data_section_type_annotations(self):
        self._write_type_annotation(RowType.HEADER)
        annotations = [RowType.DATA.value] * self.DATA_ROWS
        self.worksheet.write_column(self.row + 1, 0, annotations)

    def _write_data_column(self, entity_name: str, entity_schema: dict):
        self.worksheet.write(self.row, self.col,
                             entity_name.capitalize(), self.HEADER_THEME)
        self._write_comment(self.row, self.col, entity_schema)

        # Write validation to data cells below header cell
        data_range = xl_range(self.row + 1, self.col,
                              self.row + self.DATA_ROWS, self.col)
        self._write_validation(data_range, entity_schema)

    def _write_comment(self, row: int, col: int, entity_schema: dict):
        if 'description' in entity_schema:
            self.worksheet.write_comment(
                row, col, entity_schema['description'], self.COMMENT_THEME)

    def _write_validation(self, cell: str, entity_schema: dict):
        validation = self._get_validation(cell, entity_schema)
        validation and self.worksheet.data_validation(cell, validation)

    def _hide_type_annotations(self):
        self.worksheet.set_column(0, 0, None, None, {'hidden': True})

    @staticmethod
    def _get_validation(cell: str, property_schema: dict) -> Optional[dict]:
        property_enum = property_schema.get('enum')
        property_format = property_schema.get('format')
        property_type = property_schema.get('type')
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
        elif property_type == 'boolean':
            return {
                'validate': 'list',
                'source': ['True', 'False'],
            }

        return None

    @staticmethod
    def _make_date_validation_string(cell: str) -> str:
        return f'=AND(ISNUMBER({cell}),LEFT(CELL("format",{cell}),1)="D")'

    def _init_themes(self):
        self.TITLE_THEME = self.workbook.add_format(XlThemes.TITLE_THEME)
        self.PREAMBLE_THEME = self.workbook.add_format(XlThemes.PREAMBLE_THEME)
        self.HEADER_THEME = self.workbook.add_format(XlThemes.HEADER_THEME)
        self.DATA_THEME = self.workbook.add_format(XlThemes.DATA_THEME)
        self.DIRECTIVE_THEME = self.workbook.add_format(
            XlThemes.DIRECTIVE_THEME)
        self.COMMENT_THEME = XlThemes.COMMENT_THEME
