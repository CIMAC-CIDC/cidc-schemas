# -*- coding: utf-8 -*-

"""The underlying data representation of an assay or shipping manifest template."""

import os
import os.path
import logging
import uuid
import json
import jsonschema
from typing import List, Optional, Dict, BinaryIO, Union
from collections import OrderedDict

from .constants import SCHEMA_DIR, TEMPLATE_DIR
from .json_validation import _load_dont_validate_schema

logger = logging.getLogger("cidc_schemas.template")


def _get_template_path_map() -> dict:
    """Build a mapping from template schema types to template schema paths."""
    path_map = {}
    for template_type_dir in os.listdir(TEMPLATE_DIR):
        abs_type_dir = os.path.join(TEMPLATE_DIR, template_type_dir)
        if os.path.isdir(abs_type_dir):
            for template_file in os.listdir(abs_type_dir):
                template_type = template_file.replace("_template.json", "")
                template_schema_path = os.path.join(abs_type_dir, template_file)
                path_map[template_type] = template_schema_path

    return path_map


_TEMPLATE_PATH_MAP = _get_template_path_map()


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
        if not template_type_dir.startswith("."):
            # Create the directory for this template type
            target_subdir = os.path.join(target_dir, template_type_dir)
            if not os.path.exists(target_subdir):
                os.makedirs(target_subdir)

            schema_subdir = os.path.join(TEMPLATE_DIR, template_type_dir)

            # Create a new empty template for each template schema in schema_subdir
            for template_schema_file in os.listdir(schema_subdir):
                if not template_schema_file.startswith("."):
                    schema_path = os.path.join(schema_subdir, template_schema_file)
                    template_xlsx_file = template_schema_file.replace(".json", ".xlsx")
                    target_path = os.path.join(target_subdir, template_xlsx_file)
                    generate_empty_template(schema_path, target_path)


class Template:
    """
    Configuration describing a manifest or assay template

    Properties:
        schema {dict} -- a validated template JSON schema
        worksheets {Dict[str, dict]} -- a mapping from worksheet names to worksheet schemas
    """

    ignored_worksheets = ["Legend", "Data Dictionary"]

    def __init__(self, schema: dict, type: str, schema_root: str = SCHEMA_DIR):
        """
        Load the schema defining a manifest or assay template.

        Arguments:
            schema {dict} -- a valid JSON schema describing a template
            type -- schema file ..._template.json prefix. Used for repr.
        """
        self.schema = schema
        self.type = type
        self.schema_root = schema_root
        self.worksheets = self._extract_worksheets()
        self.key_lu = self._load_keylookup()

    def __repr__(self):
        return f"<Template({self.type})>"

    def _extract_worksheets(self) -> Dict[str, dict]:
        """Build a mapping from worksheet names to worksheet section schemas"""

        assert (
            "worksheets" in self.schema["properties"]
        ), f'{self.type} schema missing "worksheets" property'
        worksheet_schemas = self.schema["properties"]["worksheets"]

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
            if section_name == "preamble_rows":
                processed_worksheet[section_name] = process_fields(section_schema)
            elif section_name == "data_columns":
                data_schemas = {}
                for table_name, table_schema in section_schema.items():
                    data_schemas[table_name] = process_fields(table_schema)
                processed_worksheet[section_name] = data_schemas

        return processed_worksheet

    def _get_ref_coerce(self, ref: str):
        """
        This function takes a json-schema style $ref pointer,
        opens the schema and determines the best python
        function to type the value.

        Args:
            ref: /path/to/schema.json

        Returns:
            Python function pointer
        """

        referer = {"$ref": ref}

        resolver_cache = {}
        schemas_dir = f"file://{self.schema_root}/schemas"
        while "$ref" in referer:
            # get the entry
            resolver = jsonschema.RefResolver(schemas_dir, referer, resolver_cache)
            _, referer = resolver.resolve(referer["$ref"])

        entry = referer
        # add our own type conversion
        t = entry["type"]

        return Template._get_coerce(t, entry.get("$id"))

    @staticmethod
    def _gen_upload_placeholder_uuid(_):
        return str(uuid.uuid4())

    @staticmethod
    def _get_coerce(t: str, object_id=None):
        """
        This function takes a json-schema style type
        and determines the best python
        function to type the value.
        """
        # if it's an artifact that will be loaded through local file
        # we just return uuid as value
        if object_id in ["local_file_path", "local_file_path_list"]:
            return Template._gen_upload_placeholder_uuid
        if t == "string":
            return str
        elif t == "integer":
            return int
        elif t == "number":
            return float
        elif t == "boolean":
            return bool
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

        def _add_coerce(field_def: dict) -> dict:
            """ Checks if we have a cast func for that 'type_ref' """
            if "type_ref" in field_def or "$ref" in field_def:
                coerce = self._get_ref_coerce(
                    field_def.get("type_ref") or field_def["$ref"]
                )
            elif "type" in field_def:
                if "$id" in field_def:
                    coerce = self._get_coerce(field_def["type"], field_def["$id"])
                else:
                    coerce = self._get_coerce(field_def["type"])
            else:
                raise Exception(
                    f'Either "type" or "type_ref" or "$ref should be present '
                    f"in each template schema field def, but not found in {field_def!r}"
                )

            if "process_as" in field_def:

                # recursively _add_coerce to each sub 'process_as' item
                for extra_fdef in field_def["process_as"]:
                    extra_fdef.update(
                        # adding "key_name" from parent field_def
                        # so we later know what template column this came from
                        dict(_add_coerce(extra_fdef), key_name=field_def["key_name"])
                    )

            return dict(coerce=coerce, **field_def)

        # loop over each worksheet
        for ws_name, ws_schema in self.worksheets.items():

            # loop over each row in pre-amble
            for preamble_key, preamble_def in ws_schema.get(
                "preamble_rows", {}
            ).items():

                # populate lookup
                # TODO .lower() ?
                key_lu[preamble_key] = _add_coerce(
                    dict(preamble_def, key_name=preamble_key)
                )
                # we expect preamble_def from `_template.json` have 2 fields
                # (as for template.schema) - "merge_pointer" and "type_ref"

            # load the data columns
            for section_key, section_def in ws_schema.get("data_columns", {}).items():
                for column_key, column_def in section_def.items():

                    # populate lookup
                    # TODO .lower() ?
                    key_lu[column_key] = _add_coerce(
                        dict(column_def, key_name=column_key)
                    )
                    # we expect column_def from `_template.json` have 2 fields
                    # (as for template.schema) - "merge_pointer" and "type_ref"

        return key_lu

    # XlTemplateReader only knows how to format these types of sections
    VALID_WS_SECTIONS = set(
        [
            "preamble_rows",
            "data_columns",
            "prism_preamble_object_pointer",
            "prism_data_object_pointer",
            "prism_preamble_object_schema",
        ]
    )

    @staticmethod
    def _validate_worksheet(ws_title: str, ws_schema: dict):
        # Ensure all worksheet sections are supported
        ws_sections = set(ws_schema.keys())
        unknown_props = ws_sections.difference(Template.VALID_WS_SECTIONS)
        assert (
            not unknown_props
        ), f"unknown worksheet sections {unknown_props} - only {Template.VALID_WS_SECTIONS} supported"

    @staticmethod
    def from_type(template_type: str):
        """Load a Template from a template type, e.g., "pbmc" or "wes"."""
        try:
            schema_path = _TEMPLATE_PATH_MAP[template_type]
        except KeyError:
            raise NotImplementedError(f"unknown template type: {template_type}")
        return Template.from_json(schema_path, type=template_type)

    @staticmethod
    def from_json(
        template_schema_path: str, schema_root: str = SCHEMA_DIR, type: str = ""
    ):
        """
        Load a Template from a template schema.

        Arguments:
            template_schema_path {str} -- path to the template schema file
            schema_root {str} -- path to the directory where all schemas are stored
        """
        template_schema = _load_dont_validate_schema(template_schema_path, schema_root)

        return Template(
            template_schema,
            type=type
            or os.path.basename(template_schema_path).partition("_template.json")[0],
        )

    def to_excel(self, xlsx_path: str):
        """Write this `Template` to an Excel file"""
        from .template_writer import XlTemplateWriter

        XlTemplateWriter().write(xlsx_path, self)

    def validate_excel(self, xlsx: Union[str, BinaryIO]) -> bool:
        """Validate the given Excel file (either a path or an open file) against this `Template`"""
        from .template_reader import XlTemplateReader

        xlsx, errs = XlTemplateReader.from_excel(xlsx)
        if errs:
            return False
        return xlsx.validate(self)

    def iter_errors_excel(self, xlsx: Union[str, BinaryIO]) -> List[str]:
        """Produces all validation errors the given Excel file (either a path or an open file) against this `Template`"""
        from .template_reader import XlTemplateReader

        xlsx, errs = XlTemplateReader.from_excel(xlsx)
        if errs:
            return errs
        return xlsx.iter_errors(self)
