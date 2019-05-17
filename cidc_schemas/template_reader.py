# -*- coding: utf-8 -*-

"""Defines the `XlTemplateReader` class for reading/validating templates from Excel templates."""

import os
import json
import logging
from typing import Dict, List, Tuple

import openpyxl

from .template import Template
from .template_writer import RowType
from .json_validation import validate_instance

logger = logging.getLogger('cidc_schemas.template_reader')


# A template row is any tuple whose first member is a RowType
TemplateRow = Tuple[RowType, ...]

# A mapping from RowType to a list of rows with that type
RowGroup = Dict[RowType, list]


class ValidationError(Exception):
    pass


class XlTemplateReader:
    """
    Reader and validator for Excel templates.
    """

    def __init__(self, template: Dict[str, List[TemplateRow]]):
        """
        Initialize a template reader.

        Arguments:
            template {Dict[str, List[TemplateRow]]} -- a mapping from worksheet names to worksheet rows
        """
        self.template = template

        # Mapping from worksheet names to rows grouped by type
        self.grouped_rows: Dict[str, RowGroup] = self._group_worksheet_rows()

    @staticmethod
    def from_excel(xlsx_path: str):
        """
        Initialize an Excel template reader from an excel path.

        Arguments:
          xlsx_path {str} -- path to the Excel template
        """

        # Load the Excel file
        workbook = openpyxl.load_workbook(xlsx_path)

        # Extract the first worksheet
        first_sheet = workbook.sheetnames[0]
        if len(workbook.sheetnames) > 1:
            logging.warning(
                f"Found multiple worksheets in {xlsx_path} - only parsing {first_sheet}")
        worksheet = workbook[first_sheet]

        template = {}
        for worksheet_name in workbook.sheetnames:
            worksheet = workbook[worksheet_name]
            rows = []
            for i, row in enumerate(worksheet.iter_rows()):
                # Convert to string and extract type annotation
                typ, *values = [col.value for col in row]
                row_type = RowType.from_string(typ)

                # If no recognized row type found, don't parse this row
                if not row_type:
                    logger.info(
                        f'No recognized row type found in row {i + 1} - skipping')
                    continue

                # If entire row is empty, skip it (this happens at the bottom of the data table, e.g.)
                if not any(values):
                    continue

                # Reassemble parsed row and add to rows
                rows.append((row_type, *values))
            template[worksheet_name] = rows

        return XlTemplateReader(template)

    def _group_worksheet_rows(self) -> Dict[str, RowGroup]:
        """Map worksheet names to rows grouped by row type"""
        grouped_rows = {}
        for name, rows in self.template.items():
            grouped_rows[name] = self._group_rows(rows)
        return grouped_rows

    @staticmethod
    def _group_rows(rows) -> RowGroup:
        """Group rows in a worksheet by their type annotation"""
        # Initialize mapping from row types to lists of row content
        row_groups: Dict[RowType, List] = {
            row_type: [] for row_type in RowType}

        for row in rows:
            row_type, *content = row
            row_groups[row_type].append(content)

        # There should only be one header row for the data table
        assert len(row_groups[RowType.HEADER]
                   ) == 1, f"Expected exactly one header row"

        # TODO: enforce more constraints (e.g., if there are data rows,
        #       there must be a header row)

        return row_groups

    @staticmethod
    def _get_schema(key: str, schema: Dict[str, dict]) -> dict:
        """Try to find a schemas for the given template key"""
        entity_name = key.lower()
        assert entity_name in schema, f"No schema found for {key}"
        return schema[entity_name]

    def _get_data_schemas(self, row_groups, data_schemas: Dict[str, dict]) -> List[dict]:
        """Transform data table into a list of entity name + schema pairs"""
        header_row = row_groups[RowType.HEADER][0]
        data_rows = row_groups[RowType.DATA]

        # Ensure every data row has the right number of entries
        n_columns = len(header_row)
        for i, data_row in enumerate(data_rows):
            n_entries = len(data_row)
            assert n_entries == n_columns, f"The {i + 1}th data row has too few entries"

        schemas = [self._get_schema(header, data_schemas)
                   for header in header_row]
        return schemas

    def validate(self, template: Template) -> bool:
        """
        Validate a populated Excel template against a template schema.

        Arguments:
            template {Template} -- a template object containing the expected structure of the template

        Returns:
            {bool} -- True if valid, otherwise raises an exception with validation reporting
        """
        invalid_messages = []

        for name, schema in template.worksheets.items():
            errors = self._validate_worksheet(name, schema)
            invalid_messages.extend(errors)

        if invalid_messages:
            feedback = '\n'.join(invalid_messages)
            raise ValidationError('\n' + feedback)

        return True

    def _validate_worksheet(self, worksheet_name: str, ws_schema: dict) -> List[str]:
        """Validate rows in a worksheet, returning a list of validation error messages."""

        invalid_messages = []

        assert worksheet_name in self.grouped_rows, f'No worksheet found with name {worksheet_name}'
        row_groups = self.grouped_rows[worksheet_name]

        if 'preamble_rows' in ws_schema:
            # Validate preamble rows
            preamble_schemas = ws_schema['preamble_rows']
            for key, *values in row_groups[RowType.PREAMBLE]:
                value = values[0]
                schema = self._get_schema(key, preamble_schemas)
                invalid_reason = validate_instance(value, schema)

                if invalid_reason:
                    invalid_messages.append(
                        f'{worksheet_name}: Header, {key}:\t{invalid_reason}')

        if 'data_columns' in ws_schema:
            # Build up flat mapping of data schemas
            flat_data_schemas: Dict[str, dict] = {}
            for section in ws_schema['data_columns'].values():
                flat_data_schemas = {
                    **flat_data_schemas, **section}

            data_schemas = self._get_data_schemas(
                row_groups, flat_data_schemas)

            # Validate data rows
            headers = row_groups[RowType.HEADER][0]
            for data_row in row_groups[RowType.DATA]:
                for col, value in enumerate(data_row):
                    invalid_reason = validate_instance(
                        value, data_schemas[col])

                    if invalid_reason:
                        invalid_messages.append(
                            f'{worksheet_name}: Data, {headers[col]}:\t{invalid_reason}')

        return invalid_messages
