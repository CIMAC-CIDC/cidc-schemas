# -*- coding: utf-8 -*-

"""The underlying data representation of an assay or shipping manifest template."""

import os
import os.path
import logging
import uuid
import json
import jsonschema
import re
from typing import (
    List,
    Optional,
    Dict,
    BinaryIO,
    Union,
    NamedTuple,
    Any,
    Tuple,
    Callable,
)
from collections import OrderedDict, defaultdict

from .constants import SCHEMA_DIR, TEMPLATE_DIR
from .json_validation import _load_dont_validate_schema
from .util import get_file_ext

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


class AtomicChange(NamedTuple):
    """
    Represents exactly one "value set" operation on some data object
    `Pointer` being a json-pointer string showing where to set `value` to.
    """

    pointer: str
    value: Any


class LocalFileUploadEntry(NamedTuple):
    local_path: str
    gs_key: str
    upload_placeholder: str
    metadata_availability: Optional[bool]


class _FieldDef(NamedTuple):
    """
    Represents all the specs on processing a specific value 
    """

    key_name: str
    coerce: Callable
    merge_pointer: str
    # MAYBE TODO unify type and type_ref
    type: Union[str, None] = None
    type_ref: str = None
    gcs_uri_format: Union[str, dict, None] = None
    extra_metadata: bool = False
    parse_through: Union[str, None] = None
    do_not_merge: bool = False
    allow_empty: bool = False
    is_artifact: Union[str, bool] = False

    def artifact_checks(self):
        # TODO maybe move these checks to constructor?
        # Though it will require changing implementation
        # from NamedTuple to something more extensible like attrs or dataclasses
        if self.is_artifact and not self.gcs_uri_format:
            raise Exception(f"Empty gcs_uri_format")

        if self.gcs_uri_format and not self.is_artifact:
            raise Exception(f"gcs_uri_format defined for not is_artifact")

        if self.gcs_uri_format and not isinstance(self.gcs_uri_format, (dict, str)):
            raise Exception(
                f"Bad gcs_uri_format: {type(self.gcs_uri_format)} - should be dict or str."
            )

        if (
            isinstance(self.gcs_uri_format, dict)
            and "format" not in self.gcs_uri_format
        ):
            raise Exception(f"dict type gcs_uri_format should have 'format' def")

    def process_value(
        self, raw_val, format_context: dict, eval_context: dict
    ) -> Tuple[List[AtomicChange], List[LocalFileUploadEntry]]:

        logger.debug(f"Processing field spec: {self}")

        # skip nullable
        if self.allow_empty and raw_val is None:
            return [], []

        if self.do_not_merge:
            logger.debug(f"Ignoring {self.key_name!r} due to 'do_not_merge' == True")
            return [], []

        if self.parse_through:
            try:
                raw_val = eval(self.parse_through, eval_context)(raw_val)

            # catching everything, because of eval
            except Exception as e:
                _field_name = self.merge_pointer.rsplit("/", 1)[-1]
                raise ParsingException(
                    f"Cannot extract {_field_name} from {self.key_name} value: {raw_val!r} ({e})"
                ) from e

        # or set/update value in-place in data_obj dictionary

        try:
            val, files = self._calc_val_and_files(raw_val, format_context)
        except ParsingException:
            raise
        except Exception as e:
            # this shouldn't wrap all exceptions into a parsing one,
            # but we need to split calc_val_and_files to handle them separately here
            # because we still want to catch all from `.coerce`
            raise ParsingException(
                f"Can't parse {self.key_name!r} value {str(raw_val)!r}: {e}"
            ) from e

        if self.is_artifact == True:  # multi goes into other one
            placeholder_pointer = self.merge_pointer + "/upload_placeholder"
            facet_group_pointer = self.merge_pointer + "/facet_group"
            return (
                [
                    AtomicChange(placeholder_pointer, val["upload_placeholder"]),
                    AtomicChange(facet_group_pointer, val["facet_group"]),
                ],
                files,
            )
        else:
            return [AtomicChange(self.merge_pointer, val)], files

    ## TODO easy - split val coerce / files calc to handle exceptions separately
    ## TODO hard - files (artifact and multi) should be just coerce?
    def _calc_val_and_files(self, raw_val, format_context: dict):
        """
        Processes one field value based on `_FieldDef` taken from a ..._template.json schema.
        Calculates a file upload entry if is_artifact.
        """

        val = self.coerce(raw_val)

        if not self.is_artifact:
            return val, []  # no files if it's not an artifact

        files = []

        # deal with multi-artifact
        if self.is_artifact == "multi":
            logger.debug(f"      collecting multi local_file_path {self}")

            # In case of is_aritfact=multi we expect the value to be a comma-separated
            # list of local_file paths (that we will convert to uuids)
            # and also for the corresponding DM schema to be an array of artifacts
            # that we will fill with upload_placeholder uuids

            # So our value is a list of artifact placeholders
            val = []

            # and we iterate through local file paths:
            for num, local_path in enumerate(raw_val.split(",")):
                # Ignoring errors here as we're sure `coerce` will just return a uuid
                file_uuid = self.coerce(local_path)

                artifact, facet_group = self._format_single_artifact(
                    local_path=local_path,
                    uuid=file_uuid,
                    format_context=dict(
                        format_context,
                        num=num  # add num to be able to generate
                        # different gcs keys for each multi-artifact file.
                    ),
                )

                val.append(
                    {"upload_placeholder": file_uuid, "facet_group": facet_group}
                )

                files.append(artifact)

        else:
            logger.debug(f"Collecting local_file_path {self}")
            artifact, facet_group = self._format_single_artifact(
                local_path=raw_val, uuid=val, format_context=format_context
            )

            val = {"upload_placeholder": val, "facet_group": facet_group}

            files.append(artifact)

        return val, files

    def _format_single_artifact(
        self, local_path: str, uuid: str, format_context: dict
    ) -> Tuple[LocalFileUploadEntry, str]:
        """Return a LocalFileUploadEntry for this artifact, along with the artifact's facet group."""

        # By default we think gcs_uri_format is a format-string
        format = self.gcs_uri_format
        try_formatting = lambda: format.format_map(format_context)

        # or it could be a dict
        if isinstance(self.gcs_uri_format, dict):
            if "check_errors" in self.gcs_uri_format:
                # `eval` should be fine, as we're controlling the code argument in templates
                err = eval(self.gcs_uri_format["check_errors"])(local_path)
                if err:
                    raise ParsingException(err)

            format = self.gcs_uri_format["format"]
            # `eval` should be fine, as we're controlling the code argument in templates
            try_formatting = lambda: eval(format)(local_path, format_context)

        try:
            gs_key = try_formatting()
        except Exception as e:
            raise ParsingException(
                f"Can't format destination gcs uri for {self.key_name!r}: {format}"
            )

        expected_extension = get_file_ext(gs_key)
        provided_extension = get_file_ext(local_path)
        if provided_extension != expected_extension:
            raise ParsingException(
                f"Expected {'.' + expected_extension} for {self.key_name!r} but got {'.' + provided_extension!r} instead."
            )

        facet_group = _get_facet_group(format)

        return (
            LocalFileUploadEntry(
                local_path=local_path,
                gs_key=gs_key,
                upload_placeholder=uuid,
                metadata_availability=self.extra_metadata,
            ),
            facet_group,
        )


class ParsingException(ValueError):
    pass


_empty_defaultdict: Dict[str, str] = defaultdict(str)


def _get_facet_group(gcs_uri_format: str) -> str:
    """"
    Extract a file's facet group from its GCS URI format string by removing
    the "format" parts.
    """
    # Provide empty strings for a GCS URI formatter variables
    try:
        # First, attempt to call the format string as a lambda
        fmted_string = eval(gcs_uri_format)("", _empty_defaultdict)
    except:
        # Fall back to string interpolation via format_map
        fmted_string = gcs_uri_format.format_map(_empty_defaultdict)

    # Clear any double slashes
    facet_group = re.sub(r"\/\/*", "/", fmted_string)

    return facet_group


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
            elif section_name == "prism_arbitrary_data_merge_pointer":
                processed_worksheet[
                    "prism_arbitrary_data_merge_pointer"
                ] = section_schema

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

        return self._get_simple_type_coerce(t, entry.get("$id"))

    @staticmethod
    def _gen_upload_placeholder_uuid(_):
        return str(uuid.uuid4())

    @staticmethod
    def _get_simple_type_coerce(t: str, object_id=None):
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

    def _get_coerce(self, field_def: dict) -> Callable:
        """ Checks if we have a cast func for that 'type_ref' and returns it."""

        orig_fdef = dict(field_def)

        if "type_ref" in field_def or "ref" in field_def:
            coerce = self._get_ref_coerce(
                field_def.pop("ref", field_def.pop("type_ref"))
            )
        elif "type" in field_def:
            coerce = self._get_simple_type_coerce(
                field_def.pop("type"), field_def.pop("$id", None)
            )
        elif field_def.get("do_not_merge", False):

            raise Exception(
                "Template fields flagged with `do_not_merge` do not have a typecast function"
            )

        else:
            raise Exception(
                f'Either "type" or "type_ref" or "$ref" should be present '
                f"in each template schema field def, but not found in {orig_fdef!r}"
            )

        return coerce

    def _load_field_defs(self, key_name, def_dict) -> List[_FieldDef]:
        """
        Converts a template schema "field definition" to a list of typed `_FieldDef`s,
        which ensures we get only supported matching logic.
        """

        def_d = dict(def_dict)  # so we don't mutate original
        process_as = def_d.pop("process_as", [])
        res = []

        if not def_dict.get("do_not_merge"):

            # remove all unsupported _FieldDef keys
            for f in def_dict:
                if f in _FieldDef._fields:
                    continue
                def_d.pop(f, None)

            try:
                coerce = self._get_coerce(def_d)
                fd = _FieldDef(key_name=key_name, coerce=coerce, **def_d)
                fd.artifact_checks()
            except Exception as e:
                raise Exception(f"Couldn't load mapping for {key_name!r}: {e}") from e

            res.append(fd)

        # "process_as" allows to define additional places/ways to put a match
        # somewhere in the resulting doc, with additional processing.
        # E.g. we need to strip cimac_id='CM-TEST-0001-01' to 'CM-TEST-0001'
        # and put it in this sample parent's cimac_participant_id
        for extra_fdef in process_as:
            # recursively adds coerce to each sub 'process_as' item
            res.extend(self._load_field_defs(key_name, extra_fdef))

        return res

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
        key_lu = defaultdict(dict)

        # loop over each worksheet
        for ws_name, ws_schema in self.worksheets.items():

            ws_name = self._process_fieldname(ws_name)

            try:
                # loop over each row in pre-amble
                for preamble_key, preamble_def in ws_schema.get(
                    "preamble_rows", {}
                ).items():

                    key_lu[ws_name][preamble_key] = self._load_field_defs(
                        preamble_key, preamble_def
                    )

                # load the data columns
                for section_key, section_def in ws_schema.get(
                    "data_columns", {}
                ).items():
                    for column_key, column_def in section_def.items():

                        key_lu[ws_name][column_key] = self._load_field_defs(
                            column_key, column_def
                        )
            except Exception as e:
                raise Exception(
                    f"Error in template {self.type!r}/{ws_name!r}: {e}"
                ) from e

        # converting from defaultdict to just dict (of dicts)
        # to be able to catch unexpected worksheet error
        return dict(key_lu)

    @staticmethod
    def _sanitize_arbitrary_key(key):
        # TODO figure out sanitization - non-ascii or non-unicode or something
        return key

    def _process_arbitrary_val(
        self, key, raw_val, arbitrary_data_merge_pointer
    ) -> AtomicChange:
        """
        Processes one field value based on 'prism_arbitrary_data' directive in template schema.
        Calculates a list of `AtomicChange`s within a context object
        and an empty list of file upload entries.
        """

        return AtomicChange(
            arbitrary_data_merge_pointer + "/" + self._sanitize_arbitrary_key(key),
            raw_val,
        )

    def process_field_value(
        self,
        worksheet: str,
        key: str,
        raw_val,
        format_context: dict,
        eval_context: dict,
    ) -> Tuple[List[AtomicChange], List[LocalFileUploadEntry]]:
        """
        Processes one field value based on field_def taken from a template schema.
        Calculates a list of `AtomicChange`s within a context object
        and a list of file upload entries.
        A list of values and not just one value might arise from a `process_as` section
        in template schema, that allows for multi-processing of a single cell value.
        """

        logger.debug(f"Processing property {worksheet!r}:{key!r} - {raw_val!r}")
        try:
            ws_field_defs = self.key_lu[self._process_fieldname(worksheet)]
            ws = self.worksheets[worksheet]
        except KeyError:
            raise ParsingException(f"Unexpected worksheet {worksheet!r}.")

        try:
            field_defs = ws_field_defs[self._process_fieldname(key)]
        except KeyError:
            if ws.get("prism_arbitrary_data_merge_pointer"):
                return (
                    [
                        self._process_arbitrary_val(
                            key, raw_val, ws["prism_arbitrary_data_merge_pointer"]
                        )
                    ],
                    [],
                )
            else:
                raise ParsingException(f"Unexpected property {worksheet!r}:{key!r}")

        logger.debug(f"Found field {len(field_defs)} defs")

        changes, files = [], []
        for f_def in field_defs:
            try:
                chs, fs = f_def.process_value(raw_val, format_context, eval_context)
            except Exception as e:
                raise ParsingException(e)

            changes.extend(chs)
            files.extend(fs)

        return changes, files

    # XlTemplateReader only knows how to format these types of sections
    VALID_WS_SECTIONS = set(
        [
            "preamble_rows",
            "data_columns",
            "prism_preamble_object_pointer",
            "prism_data_object_pointer",
            "prism_preamble_object_schema",
            "prism_arbitrary_data_section",
            "prism_arbitrary_data_merge_pointer",
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
