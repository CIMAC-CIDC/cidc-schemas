# -*- coding: utf-8 -*-

"""The underlying data representation of an assay or shipping manifest template."""

import os
import os.path
import logging
import uuid
import json
import jsonschema
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
    # TODO unwrap local_file
    gcs_uri_format: Union[str, dict]
    extra_metadata: bool
    coerce: Callable
    description: str
    type: str
    # # TODO join type and type_ref by resolving ref
    # type_ref: str
    merge_pointer: str
    enum: Any
    format: Any
    example: Any
    # TODO remove?
    in_doc_ref_pattern: str
    parse_through: str
    do_not_merge: bool
    allow_empty: bool
    is_artifact: bool


class ParsingException(ValueError):
    pass


def _format_single_artifact(
    local_path: str, uuid: str, field_def: _FieldDef, format_context: dict
) -> Tuple[LocalFileUploadEntry, str]:
    """Return a LocalFileUploadEntry for this artifact, along with the artifact's facet group."""

    # TODO move these check (for `is_artifact`s to template reading)
    if not field_def.gcs_uri_format:
        raise Exception(f"Empty gcs_uri_format for {field_def.key_name!r}") from e
    if not isinstance(gcs_uri_format, (dict, str)):
        raise Exception(f"Unsupported gcs_uri_format for {field_def.key_name!r}")

    if isinstance(gcs_uri_format, dict):
        if "check_errors" in gcs_uri_format:
            # `eval` should be fine, as we're controlling the code argument in templates
            err = eval(gcs_uri_format["check_errors"])(local_path)
            if err:
                raise ParsingException(err)

        try:
            gs_key = eval(gcs_uri_format["format"])(local_path, format_context)
            facet_group = _get_facet_group(gcs_uri_format["format"])
        except Exception as e:
            raise ParsingException(
                f"Can't format gcs uri for {field_def.key_name!r}: {gcs_uri_format['format']}: {e!r}"
            )

    elif isinstance(gcs_uri_format, str):
        try:
            gs_key = gcs_uri_format.format_map(format_context)
            facet_group = _get_facet_group(gcs_uri_format)
        except KeyError as e:
            raise ParsingException(
                f"Can't format gcs uri for {field_def.key_name!r}: {gcs_uri_format}: {e!r}"
            )

        expected_extension = _get_file_ext(gs_key)
        provided_extension = _get_file_ext(local_path)
        if provided_extension != expected_extension:
            raise ParsingException(
                f"Expected {'.' + expected_extension} for {field_def.key_name!r} but got {'.' + provided_extension!r} instead."
            )

    return (
        LocalFileUploadEntry(
            local_path=local_path,
            gs_key=gs_key,
            upload_placeholder=uuid,
            metadata_availability=field_def.extra_metadata,
        ),
        facet_group,
    )


def _calc_val_and_files(raw_val, field_def: _FieldDef, format_context: dict):
    """
    Processes one field value based on field_def taken from a ..._template.json schema.
    Calculates a value and (if there's 'is_artifact') a file upload entry.
    """

    val = field_def.coerce(raw_val)

    if not field_def.is_artifact:
        return val, []  # no files if it's not an artifact

    files = []

    # deal with multi-artifact
    if field_def.is_artifact == "multi":
        logger.debug(f"      collecting multi local_file_path {field_def}")

        # In case of is_aritfact=multi we expect the value to be a comma-separated
        # list of local_file paths (that we will convert to uuids)
        # and also for the corresponding DM schema to be an array of artifacts
        # that we will fill with upload_placeholder uuids

        # So our value is a list of artifact placeholders
        val = []

        # and we iterate through local file paths:
        for num, local_path in enumerate(raw_val.split(",")):
            # Ignoring errors here as we're sure `coerce` will just return a uuid
            file_uuid = coerce(local_path)

            artifact, facet_group = _format_single_artifact(
                local_path=local_path,
                uuid=file_uuid,
                field_def=field_def,
                format_context=dict(
                    format_context,
                    num=num  # add num to be able to generate
                    # different gcs keys for each multi-artifact file.
                ),
            )

            val.append({"upload_placeholder": file_uuid, "facet_group": facet_group})

            files.append(artifact)

    else:
        logger.debug(f"Collecting local_file_path {field_def}")
        artifact, facet_group = _format_single_artifact(
            local_path=raw_val,
            uuid=val,
            field_def=field_def,
            format_context=format_context,
        )

        val = {"upload_placeholder": val, "facet_group": facet_group}

        files.append(artifact)

    return val, files


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

    def _add_coerce(self, field_def: dict) -> dict:
        """ Checks if we have a cast func for that 'type_ref' """

        orig_fdef = dict(field_def)

        if "type_ref" in field_def:
            coerce = self._get_ref_coerce(field_def.pop("type_ref"))
        elif "ref" in field_def:
            coerce = self._get_ref_coerce(field_def.pop("ref"))
        elif "type" in field_def:
            coerce = self._get_coerce(field_def.pop("type"), field_def.pop("$id", None))
        elif field_def.do_not_merge:

            def c(v):
                raise Exception("Should not have been merged as for `do_not_merge`")

            coerce = c

        else:
            raise Exception(
                f'Either "type" or "type_ref" or "$ref should be present '
                f"in each template schema field def, but not found in {orig_fdef!r}"
            )

        return dict(coerce=coerce, **field_def)

    def _load_f_defs(self, key_name, def_dict):
        # TODO check types, add defaults ?

        def_dict = dict(def_dict)  # so we don't mutate original
        def_dict.pop("$comment", None)
        def_dict.pop("pattern", None)
        def_dict.pop("title", None)
        process_as = def_dict.pop("process_as", None)

        try:
            with_coerce = self._add_coerce(def_dict)
        except Exception as e:
            raise Exception(f"{key_name!r} " + str(e))

        res = [
            _FieldDef(
                key_name=key_name,
                gcs_uri_format=with_coerce.pop("gcs_uri_format", None),
                extra_metadata=with_coerce.pop("extra_metadata", None),
                enum=with_coerce.pop("enum", None),
                format=with_coerce.pop("format", None),
                description=with_coerce.pop("description", None),
                type=with_coerce.pop("type", None),
                example=with_coerce.pop("example", None),
                in_doc_ref_pattern=with_coerce.pop("in_doc_ref_pattern", None),
                parse_through=with_coerce.pop("parse_through", None),
                do_not_merge=with_coerce.pop("do_not_merge", None),
                allow_empty=with_coerce.pop("allow_empty", None),
                is_artifact=with_coerce.pop("is_artifact", None),
                merge_pointer=with_coerce.pop("merge_pointer", None),
                **with_coerce,
            )
        ]

        # "process_as" allows to define additional places/ways to put a match
        # somewhere in the resulting doc, with additional processing.
        # E.g. we need to strip cimac_id='CM-TEST-0001-01' to 'CM-TEST-0001'
        # and put it in this sample parent's cimac_participant_id

        if process_as:
            # recursively _add_coerce to each sub 'process_as' item
            for extra_fdef in process_as:
                res.extend(self._load_f_defs(key_name, extra_fdef))

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
        if self.schema.get("allow_arbitrary_data_columns"):
            key_lu = defaultdict(lambda: dict(coerce=lambda x: x))
        else:
            key_lu = {}

        # loop over each worksheet
        for ws_name, ws_schema in self.worksheets.items():

            # loop over each row in pre-amble
            for preamble_key, preamble_def in ws_schema.get(
                "preamble_rows", {}
            ).items():

                # TODO .lower() ?
                key_lu[preamble_key] = self._load_f_defs(preamble_key, preamble_def)

            # load the data columns
            for section_key, section_def in ws_schema.get("data_columns", {}).items():
                for column_key, column_def in section_def.items():

                    # TODO .lower() ?
                    key_lu[column_key] = self._load_f_defs(column_key, column_def)

        return key_lu

    def process_field_value(
        self, key: str, raw_val, format_context: dict, eval_context: dict
    ) -> Tuple[List[AtomicChange], List[LocalFileUploadEntry]]:
        """
        Processes one field value based on field_def taken from a template schema.
        Calculates a list of `AtomicChange`s within a context object
        and a list of file upload entries.
        A list of values and not just one value might arise from a `process_as` section
        in template schema, that allows for multi-processing of a single cell value.
        """

        logger.debug(f"Processing property {key!r} - {raw_val!r}")
        try:
            field_defs = self.key_lu[key.lower()]
        except KeyError:
            raise ParsingException(f"Unexpected property {key!r}.")

        logger.debug(f"Found field {len(field_defs)} defs")

        changes, files = [], []
        for f_def in field_defs:
            chs, fs = self._process_one_field_def(
                key, raw_val, f_def, format_context, eval_context
            )

            changes.extend(chs)
            fs.extend(fs)

        return changes, files

    def _process_one_field_def(
        self,
        key: str,
        raw_val,
        field_def: _FieldDef,
        format_context: dict,
        eval_context: dict,
    ) -> Tuple[List[AtomicChange], List[LocalFileUploadEntry]]:

        logger.debug(f"Processing field spec: {field_def}")

        # skip nullable
        if field_def.allow_empty:
            if raw_val is None:
                return [], []

        if field_def.do_not_merge:
            logger.debug(
                f"Ignoring {field_def.key_name!r} due to 'do_not_merge' == True"
            )
            return [], []

        if field_def.parse_through:
            try:
                raw_val = eval(field_def.parse_through, eval_context)(raw_val)

            # catching everything, because of eval
            except Exception as e:
                _field_name = field_def.merge_pointer.rsplit("/", 1)[-1]
                raise ParsingException(
                    f"Cannot extract {_field_name} from {key} value: {raw_val!r} ({e})"
                ) from e

        # or set/update value in-place in data_obj dictionary

        try:
            val, files = _calc_val_and_files(raw_val, field_def, format_context)
        except ParsingException:
            raise
        # except Exception as e: # this shouldn't wrap all exceptions into a parsing one.
        #     raise ParsingException(
        #         f"Can't parse {key!r} value {str(raw_val)!r}: {e}"
        #     ) from e

        if field_def.is_artifact:
            placeholder_pointer = field_def.merge_pointer + "/upload_placeholder"
            facet_group_pointer = field_def.merge_pointer + "/facet_group"
            return (
                [
                    AtomicChange(placeholder_pointer, val["upload_placeholder"]),
                    AtomicChange(facet_group_pointer, val["facet_group"]),
                ],
                files,
            )
        else:
            return [AtomicChange(field_def.merge_pointer, val)], files

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
