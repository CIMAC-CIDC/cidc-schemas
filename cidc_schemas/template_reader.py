# -*- coding: utf-8 -*-

"""Defines the `XlTemplateReader` class for reading/validating manifests from Excel templates."""

import os
import json
import logging
from typing import Dict, List, Tuple

import openpyxl

from .manifest import ShippingManifest
from .template_writer import RowType
from .validation import validate_instance

logger = logging.getLogger('cidc_schemas.template_reader')


# A template row is any tuple whose first member is a RowType
ManifestRow = Tuple[RowType, ...]


class XlTemplateReader:
    """
    Reader and validator for Excel manifest templates.
    """

    def __init__(self, rows: List[ManifestRow]):
        """
        Initialize a manifest reader from a list of manifest rows.

        Arguments:
            rows {List[ManifestRow]} -- a list of manifest rows
        """
        self.rows = rows
        self.row_groups = self._group_rows()

    @staticmethod
    def from_excel(xlsx_path: str):
        """
        Initialize an Excel manifest reader from an excel path.

        Arguments:
          xlsx_path {str} -- path to the Excel manifest
        """

        # Load the Excel file
        workbook = openpyxl.load_workbook(xlsx_path)

        # Extract the first worksheet
        first_sheet = workbook.sheetnames[0]
        if len(workbook.sheetnames) > 1:
            logging.warning(
                f"Found multiple worksheets in {xlsx_path} - only parsing {first_sheet}")
        worksheet = workbook[first_sheet]

        rows = worksheet.iter_rows()
        return XlTemplateReader(rows)

    def _group_rows(self) -> Dict[RowType, List]:
        """Group rows in a worksheet by their type annotation"""

        # Initialize mapping from row types to lists of row content
        row_groups: Dict[RowType, List] = {
            row_type: [] for row_type in RowType}

        for row in self.rows:
            row_type, *content = row
            row_groups[row_type].append(content)

        # There should only be one header row for the data table
        assert len(row_groups[RowType.HEADER]
                   ) == 1, f"Expected exactly one header row"

        # TODO: enforce more constraints (e.g., if there are data rows,
        #       there must be a header row)

        return row_groups

    @staticmethod
    def _get_schema(key: str, manifest: ShippingManifest) -> dict:
        """Try to find a schemas for the given manifest key"""
        entity_name = key.lower()

        property_schemas = {}
        for prop in manifest.schemas.values():
            property_schemas = {**property_schemas, **prop['properties']}

        assert entity_name in property_schemas, f"No schema found for {key}"

        return property_schemas[entity_name]

    def get_data_schemas(self, manifest: ShippingManifest) -> List[dict]:
        """Transform data table into a list of entity name + value pairs"""
        header_row = self.row_groups[RowType.HEADER][0]
        data_rows = self.row_groups[RowType.DATA]

        # Ensure every data row has the right number of entries
        n_columns = len(header_row)
        for i, data_row in enumerate(data_rows):
            n_entries = len(data_row)
            assert n_entries == n_columns, f"The {i + 1}th data row has too few entries"

        schemas = [self._get_schema(header, manifest) for header in header_row]
        return schemas

    def validate(self, manifest: ShippingManifest) -> bool:
        """
        Validate Excel manifest against a manifest template

        Arguments:
            manifest {ShippingManifest} -- a manifest object containing the expected structure of the template
        """
        all_valid = True

        def kv_error(key, value):
            return f'value {value} for {key}'

        # Validate preamble rows
        for key, value in self.row_groups[RowType.PREAMBLE]:
            schema = self._get_schema(key, manifest)
            invalid_reason = validate_instance(value, schema)

            if invalid_reason:
                all_valid = False
                logger.error(
                    f'Header: {kv_error(key, value)}: {invalid_reason}')

        # Validate data rows
        data_schemas = self.get_data_schemas(manifest)
        headers = self.row_groups[RowType.HEADER][0]
        for row, data_row in enumerate(self.row_groups[RowType.DATA]):
            for col, value in enumerate(data_row):
                invalid_reason = validate_instance(value, data_schemas[col])

                if invalid_reason:
                    all_valid = False
                    err = kv_error(headers[col], value)
                    logger.error(
                        f'Data: {err}: {invalid_reason}')

        return all_valid
