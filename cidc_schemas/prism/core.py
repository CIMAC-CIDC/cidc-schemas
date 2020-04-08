"""Build metadata dictionaries from Excel files."""

import json
import logging
from typing import Any, List, NamedTuple, Tuple, Union, Optional

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.template_writer import RowType
from cidc_schemas.constants import SCHEMA_DIR
from jsonmerge import Merger, strategies, exceptions as jsonmerge_exceptions
from jsonpointer import EndOfList, JsonPointer, JsonPointerException, resolve_pointer

from .constants import SUPPORTED_TEMPLATES

logger = logging.getLogger(__file__)


def _set_val(
    pointer: str,
    val: object,
    context: dict,
    root: Union[dict, None] = None,
    context_pointer: Union[str, None] = None,
):
    """
    This function given a *pointer* (jsonpointer RFC 6901 or relative json pointer)
    to a property in a python object, sets the supplied value
    in-place in the *context* object within *root* object.
    The object we are adding data to is *root*. The object
    may or may not have any of the intermediate structure
    to fully insert the desired property.
    For example: consider
    pointer = "0/prop1/prop2"
    val = {"more": "props"}
    context = {"Pid": 1}
    root = {"participants": [context]}
    context_pointer = "/participants/0"


    First we see an `0` in pointer which denotes update
    should be within context. So no need to jump higher than context.

    So we truncate path to = "prop1/prop2"
    We see it's a string, so we know we are entering object's *prop1* as a property:
        {
            "participants": [{
                "prop1": ...
            }]
        }
    It's our whole Trial object, and ... here denotes our current descend.
    Now we truncate path one step further to = "prop2"
    Go down there and set `val={"more": "props"}` :
        {
            "participants": [{
                "prop1": {
                    "prop2": {"more": "props"}
                }
            }]
        }
    While context is a sub-part of that:
            {
                "prop1": {
                    "prop2": {"more": "props"}
                }
            }

    Args:
        pointer: relative jsonpointer to the property being set within current `context`
        val: the value being set
        context: the python object relatively to which val is being set
        root: the whole python object being constructed, contains `context`
        context_pointer: jsonpointer of `context` within `root`. Needed to jump up.
    Returns:
       Nothing
    """

    # don't do anything for None value, asserting None is permissable
    # is handled by the "allow_empty" functionality.
    if val is None:
        return

    # special case to set context doc itself
    if pointer.rstrip("#") == "":
        context.update(val)
        return

    # fill defaults
    if root is None:
        root = context
    if context_pointer is None:
        context_pointer = "/"

    # first we need to convert pointer to an absolute one
    # if it was a relative one (https://tools.ietf.org/id/draft-handrews-relative-json-pointer-00.html)
    if pointer.startswith("/"):
        jpoint = JsonPointer(pointer)
        doc = context

    else:
        # parse "relative" jumps up
        jumpups, slash, rem_pointer = pointer.partition("/")
        try:
            jumpups = int(jumpups.rstrip("#"))
        except ValueError:
            jumpups = 0

        # check that we don't have to jump up more than we dived in already
        assert jumpups <= context_pointer.rstrip("/").count(
            "/"
        ), f"Can't set value for pointer {pointer} too many jumps up from current context."

        # and we'll go down remaining part of `pointer` from there
        jpoint = JsonPointer(slash + rem_pointer)
        if jumpups > 0:
            # new context pointer
            higher_context_pointer = "/".join(
                context_pointer.strip("/").split("/")[: -1 * jumpups]
            )
            # making jumps up, by going down context_pointer but no all the way down
            if higher_context_pointer == "":
                doc = root
                assert (
                    len(jpoint.parts) > 0
                ), f"Can't update root object (pointer {pointer})"
            else:
                try:
                    doc = resolve_pointer(root, "/" + higher_context_pointer)
                except Exception as e:
                    raise Exception(e)
        else:
            doc = context

    jp_parts = jpoint.parts

    # then we update it
    for i, part in enumerate(jp_parts[:-1]):

        try:
            doc = jpoint.walk(doc, part)

        except (JsonPointerException, IndexError) as e:
            # means that there isn't needed sub-object in place, so create one

            # look ahead to figure out a proper type that needs to be created
            next_thing = __jpointer_get_next_thing(jp_parts[i + 1])

            # insert it
            __jpointer_insert_next_thing(doc, jpoint, part, next_thing)

            # and `walk` it again - this time should be OK
            doc = jpoint.walk(doc, part)

        if isinstance(doc, EndOfList):
            actual_doc = __jpointer_get_next_thing(jp_parts[i + 1])
            __jpointer_insert_next_thing(doc.list_, jpoint, "-", actual_doc)
            doc = actual_doc

    __jpointer_insert_next_thing(doc, jpoint, jp_parts[-1], val)


def __jpointer_get_next_thing(next_part) -> Union[dict, list]:
    """
    Looking at next part of pointer creates a proper object - dict or list
    to insert into a doc, that is being `jsonpointer.walk`ed.
    """
    # `next_part` looks like array index like"[0]" or "-" (RFC 6901)
    if next_part == "-" or JsonPointer._RE_ARRAY_INDEX.match(str(next_part)):
        # so create array
        return []
    # or just dict as default
    else:
        return {}


def __jpointer_insert_next_thing(doc, jpoint, part, next_thing):
    """
    Puts next_thing into a doc (that is being `jsonpointer.walk`ed)
    by *part* "address". *jpoint* is Jsonpointer that is walked.
    """

    if part == "-":
        doc.append(next_thing)
    else:
        # part will return str or int, so we can use it for `doc[typed_part]`
        # and it will work for both - doc being `dict` or `array`
        typed_part = jpoint.get_part(doc, part)
        try:

            # check if something is there.
            if isinstance(typed_part, int):

                if isinstance(doc[typed_part], dict):

                    # merge the dictionaries.
                    doc[typed_part].update(next_thing)

                else:
                    # assign it
                    doc[typed_part] = next_thing

            else:
                # assign it
                doc[typed_part] = next_thing

        # if doc is an empty array we hit an error when we try to paste to [0] index,
        # so just append
        except IndexError:
            doc.append(next_thing)


class LocalFileUploadEntry(NamedTuple):
    local_path: str
    gs_key: str
    upload_placeholder: str
    metadata_availability: Optional[bool]


def _process_property(
    key: str,
    raw_val,
    key_lu: dict,
    data_obj: dict,
    format_context: dict,
    root_obj: Union[None, dict] = None,
    data_obj_pointer: Union[None, str] = None,
) -> List[LocalFileUploadEntry]:
    """
    Takes a single property (key, val) from spreadsheet, determines
    where it needs to go in the final object, then inserts it.
    Args:
        key: property name,
        raw_val: value of a property being processed,
        key_lu: dictionary to translate from template naming to json-schema
                property names
        data_obj: dictionary we are building to represent data
        format_context: dictionary of everything needed for 'gcs_uri_format'
                        in case this property has that
        root_obj: root dictionary we are building to represent data,
                  that holds 'data_obj' within 'data_obj_pointer'
        data_obj_pointer: pointer of 'data_obj' within 'root_obj'.
                          this will allow to process relative json-pointer properties
                          to jump out of data_object
    Returns:
        [ LocalFileUploadEntry(
            local_path = "/local/file/from/excel/file/cell",
            gs_key = "constructed/GCS/path/where/this/artifact/should/endup",
            upload_placeholder = 'uuiduuiduuid-uuid-uuid-uuiduuid' # unique artifact/upload_placeholder,
            metadata_availability = boolean to indicate whether LocalFileUploadEntry should be extracted for metadata files
        ) ]
    """

    logger.debug(f"    processing property {key!r} - {raw_val!r}")
    # coerce value
    try:
        field_def = key_lu[key.lower()]
    except Exception:
        raise ParsingException(f"Unexpected property {key!r}.")

    logger.debug(f"      found def {field_def}")

    changes, files = _process_field_value(
        key=key, raw_val=raw_val, field_def=field_def, format_context=format_context
    )

    for ch in changes:
        _set_val(ch.pointer, ch.value, data_obj, root_obj, data_obj_pointer)

    return files


class _AtomicChange(NamedTuple):
    """
    Represents exactly one "value set" operation on some data object
    `Pointer` being a json-pointer string showing where to set `value` to.
    """

    pointer: str
    value: Any


def _process_field_value(
    key: str, raw_val, field_def: dict, format_context: dict
) -> Tuple[List[_AtomicChange], List[LocalFileUploadEntry]]:
    """
    Processes one field value based on field_def taken from a ..._template.json schema.
    Calculates a list of `_AtomicChange`s within a context object
    and a list of file upload entries.
    A list of values and not just one value might arise from a `process_as` section
    in template schema, that allows for multi-processing of a single cell value.
    """

    changes, files = [], []

    # skip nullable
    if field_def.get("allow_empty"):
        if raw_val is None:
            return changes, files

    if field_def.get("do_not_merge") == True:
        logger.debug(
            f"Ignoring {field_def['key_name']!r} due to 'do_not_merge' == True"
        )
    else:
        # or set/update value in-place in data_obj dictionary
        pointer = field_def["merge_pointer"]
        if field_def.get("is_artifact") == 1:
            pointer += "/upload_placeholder"

        try:
            val, files = _calc_val_and_files(raw_val, field_def, format_context)
        except ParsingException:
            raise
        except Exception as e:
            raise ParsingException(
                f"Can't parse {key!r} value {str(raw_val)!r}: {e}"
            ) from e

        changes = [_AtomicChange(pointer, val)]

    # "process_as" allows to define additional places/ways to put that match
    # somewhere in the resulting doc, with additional processing.
    # E.g. we need to strip cimac_id='CM-TEST-0001-01' to 'CM-TEST-0001'
    # and put it in this sample parent's cimac_participant_id
    if "process_as" in field_def:
        for extra_fdef in field_def["process_as"]:
            # Calculating new "raw" val.
            extra_fdef_raw_val = raw_val

            # `eval` should be fine, as we're controlling the code argument in templates
            if "parse_through" in extra_fdef:
                try:
                    extra_fdef_raw_val = eval(extra_fdef["parse_through"])(raw_val)

                # catching everything, because of eval
                except:
                    extra_field_key = extra_fdef["merge_pointer"].rsplit("/", 1)[-1]
                    raise ParsingException(
                        f"Cannot extract {extra_field_key} from {key} value: {raw_val!r}"
                    )

            # recursive call
            extra_changes, extra_files = _process_field_value(
                key=key,
                raw_val=extra_fdef_raw_val,  # new "raw" val
                field_def=extra_fdef,  # merged field_def
                format_context=format_context,
            )

            files.extend(extra_files)
            changes.extend(extra_changes)

    return changes, files


def _get_file_ext(fname):
    return fname.rsplit(".")[-1]


def _format_single_artifact(
    local_path: str, uuid: str, field_def: dict, format_context: dict
):
    try:
        gcs_uri_format = field_def["gcs_uri_format"]
    except KeyError as e:
        raise KeyError(f"Empty gcs_uri_format for {field_def['key_name']!r}") from e

    assert isinstance(
        gcs_uri_format, (dict, str)
    ), f"Unsupported gcs_uri_format for {field_def['key_name']!r}"

    if isinstance(gcs_uri_format, dict):
        if "check_errors" in gcs_uri_format:
            # `eval` should be fine, as we're controlling the code argument in templates
            err = eval(gcs_uri_format["check_errors"])(local_path)
            if err:
                raise ParsingException(err)

        try:
            gs_key = eval(gcs_uri_format["format"])(local_path, format_context)
        except Exception as e:
            raise ValueError(
                f"Can't format gcs uri for {field_def['key_name']!r}: {gcs_uri_format['format']}: {e!r}"
            )

    elif isinstance(gcs_uri_format, str):
        try:
            gs_key = gcs_uri_format.format_map(format_context)
        except KeyError as e:
            raise KeyError(
                f"Can't format gcs uri for {field_def['key_name']!r}: {gcs_uri_format}: {e!r}"
            )

        expected_extension = _get_file_ext(gs_key)
        provided_extension = _get_file_ext(local_path)
        if provided_extension != expected_extension:
            raise ParsingException(
                f"Expected {'.' + expected_extension} for {field_def['key_name']!r} but got {'.' + provided_extension!r} instead."
            )

    return LocalFileUploadEntry(
        local_path=local_path,
        gs_key=gs_key,
        upload_placeholder=uuid,
        metadata_availability=field_def.get("extra_metadata"),
    )


def _calc_val_and_files(raw_val, field_def: dict, format_context: dict):
    """
    Processes one field value based on field_def taken from a ..._template.json schema.
    Calculates a value and (if there's 'is_artifact') a file upload entry.
    """

    coerce = field_def["coerce"]
    val = coerce(raw_val)
    files = []

    if not field_def.get("is_artifact"):
        return val, files  # no files if it's not an artifact

    # deal with multi-artifact
    if field_def["is_artifact"] == "multi":
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

            val.append({"upload_placeholder": file_uuid})

            files.append(
                _format_single_artifact(
                    local_path=local_path,
                    uuid=file_uuid,
                    field_def=field_def,
                    format_context=dict(
                        format_context,
                        num=num  # add num to be able to generate
                        # different gcs keys for each multi-artifact file.
                    ),
                )
            )

    else:
        logger.debug(f"      collecting local_file_path {field_def}")
        files.append(
            _format_single_artifact(
                local_path=raw_val,
                uuid=val,
                field_def=field_def,
                format_context=format_context,
            )
        )

    return val, files


class ParsingException(ValueError):
    pass


PRISM_PRISMIFY_STRATEGIES = {"overwriteAny": strategies.Overwrite()}


def prismify(
    xlsx: XlTemplateReader,
    template: Template,
    schema_root: str = SCHEMA_DIR,
    debug: bool = False,
) -> (dict, List[LocalFileUploadEntry], List[Union[Exception, str]]):
    """
    Converts excel file to json object. It also identifies local files
    which need to uploaded to a google bucket and provides some logic
    to help build the bucket url.
    e.g. file list
    [
        {
            'local_path': '/path/to/fwd.fastq',
            'gs_key': '10021/CTTTPPPSS/wes_forward.fastq'
        }
    ]
    Args:
        xlsx: cidc_schemas.template_reader.XlTemplateReader instance
        template: cidc_schemas.template.Template instance
        schema_root: path to the target JSON schema, defaulting to CIDC schemas root
    Returns:
        (tuple):
            arg1: clinical trial object with data parsed from spreadsheet
            arg2: list of LocalFileUploadEntries that describe each file identified:
                LocalFileUploadEntry(
                    local_path = "/local/path/to/a/data/file/parsed/from/template",
                    gs_key = "constructed/relative/to/clinical/trial/GCS/path",
                    upload_placeholder = "random_uuid-for-artifact-upload",
                    metadata_availability = boolean to indicate whether LocalFileUploadEntry should be extracted for metadata files
                )
            arg3: list of errors
    Process:
    * checks out `prism_preamble_object_pointer` which is a "standard"/absolute
    rfc6901 json-pointer from CT root object to a new assay location.
    E.g. for WES it is `/assays/wes/0`, in DeepDiff terms `ct["assays"]["wes"][0]`
    * creates such "parent/preamble" object.
    E.g. for WES an object that corresponds to a wes_assay will be created:
        {
          "assays": {
            "wes": [
              {
                ...    # we're here - this is "preamble" obj = "assay" obj
              }
            ]
          }
        }
    * then processes all "preamble_rows" properties from "..._template.json"
    to fill object's properties. It uses "merge_pointer"s relative to this
    "parent/preamble" object to determine exact location where to set value.
    In most cases it's just "0/field_name". Where "0" denotes that "field_name"
    is a field in the current object.
    With exceptions like - "3/protocol_identifier" which says basically
    "go 3 levels up in the hierarchy and take protocol_identifier field of the root".
    E.g. WES:
        {
          "protocol_identifier": "4412" # from `3/protocol_identifier`
          "assays": {
            "wes": [
              {
                "assay_creator": "DFCI" # from `0/assay_creator`
              }
            ]
          }
        }
    * then it goes in a loop over all "record" rows in .xlsx, and creates
    an object within that "parent" object for each row. These "record-objects"
    are created at "prism_data_object_pointer" location relative to "preamble".

    E.g. for WES: `"prism_data_object_pointer" : "/records/-"`
        {
          "assays": {
            "wes": [
              {
                "assay_creator": "DFCI",
                "records": [
                  {
                    ...    # we're here - this is "record" obj = "assay entry" obj
                  }
                ]
              }
            ]
          }
        }
    NB Minus sign at the end of "/records/-" is a special relative-json-pointer
    notation that means we need to create new object in an 'record' array.
    So it's like if python's `l.append(v)` would've been `l[-] = v`.
    * Prism now uses those "merge_pointer" relative to this "record" object,
    to populate field values of a "record" in the same way as with "preamble".
    E.g. for WES: `"prism_data_object_pointer" : "/records/-"`
        {
          "assays": {
            "wes": [
              {
                "assay_creator": "DFCI",
                "records": [
                  {
                    "cimac_id": ...                 # from "0/cimac_id",
                    "enrichment_vendor_lot": ...    # from "0/enrichment_vendor_lot",
                    "capture_date": ...             # from "0/capture_date",
                  }
                ]
              }
            ]
          }
        }
    * Finally, as there were many "records" object created/populated,
    Prism now uses `prism_preamble_object_schema` to merge all that together
    with respect to `mergeStrategy`es defined in that schema.
    """

    if template.type not in SUPPORTED_TEMPLATES:
        raise NotImplementedError(
            f"{template.type!r} is not supported, only {SUPPORTED_TEMPLATES} are."
        )

    errors_so_far = []

    # get the root CT schema
    root_ct_schema_name = (
        template.schema.get("prism_template_root_object_schema")
        or "clinical_trial.json"
    )
    root_ct_schema = load_and_validate_schema(root_ct_schema_name, schema_root)
    # create the result CT dictionary
    root_ct_obj = {}
    template_root_obj_pointer = template.schema.get(
        "prism_template_root_object_pointer", ""
    )
    if template_root_obj_pointer != "":
        template_root_obj = {}
        _set_val(template_root_obj_pointer, template_root_obj, root_ct_obj)
    else:
        template_root_obj = root_ct_obj

    # and merger for it
    root_ct_merger = Merger(root_ct_schema, strategies=PRISM_PRISMIFY_STRATEGIES)
    # and where to collect all local file refs
    collected_files = []

    # loop over spreadsheet worksheets
    for ws_name, ws in xlsx.grouped_rows.items():
        logger.debug(f"next worksheet {ws_name!r}")

        # Here we take only first two cells from preamble as key and value respectfully,
        # lowering keys to match template schema definitions.
        preamble_context = dict(
            (r.values[0].lower(), r.values[1]) for r in ws.get(RowType.PREAMBLE, [])
        )
        # We need this full "preamble dict" (all key-value pairs) prior to processing
        # properties from data_columns or preamble wrt template schema definitions, because
        # there can be a 'gcs_uri_format' that needs to have access to all values.

        templ_ws = template.schema["properties"]["worksheets"].get(ws_name)
        if not templ_ws:
            if ws_name in template.ignored_worksheets:
                continue

            errors_so_far.append(f"Unexpected worksheet {ws_name!r}.")
            continue

        preamble_object_schema = load_and_validate_schema(
            templ_ws.get("prism_preamble_object_schema", root_ct_schema_name),
            schema_root,
        )
        preamble_merger = Merger(
            preamble_object_schema, strategies=PRISM_PRISMIFY_STRATEGIES
        )
        preamble_object_pointer = templ_ws.get("prism_preamble_object_pointer", "")
        data_object_pointer = templ_ws["prism_data_object_pointer"]

        # creating preamble obj
        preamble_obj = {}

        # Processing data rows first
        data = ws[RowType.DATA]
        if data:
            # get the data
            headers = ws[RowType.HEADER][0]

            # for row in data:
            for row in data:

                logging.debug(f"  next data row {row!r}")

                # creating data obj
                data_obj = {}
                copy_of_preamble = {}
                _set_val(
                    data_object_pointer,
                    data_obj,
                    copy_of_preamble,
                    template_root_obj,
                    preamble_object_pointer,
                )

                # We create this "data record dict" (all key-value pairs) prior to processing
                # properties from data_columns wrt template schema definitions, because
                # there can be a 'gcs_uri_format' that needs to have access to all values.
                local_context = dict(
                    zip([h.lower() for h in headers.values], row.values)
                )

                # create dictionary per row
                for key, val in zip(headers.values, row.values):

                    try:
                        # get corr xsls schema type
                        new_files = _process_property(
                            key,
                            val,
                            key_lu=template.key_lu,
                            data_obj=data_obj,
                            format_context=dict(
                                local_context, **preamble_context
                            ),  # combine contexts
                            root_obj=copy_of_preamble,
                            data_obj_pointer=data_object_pointer,
                        )
                        if new_files:
                            collected_files.extend(new_files)
                    except ParsingException as e:
                        errors_so_far.append(e)

                logger.debug("  merging preambles")
                logger.debug(f"   {preamble_obj}")
                logger.debug(f"   {copy_of_preamble}")
                preamble_obj = preamble_merger.merge(preamble_obj, copy_of_preamble)
                logger.debug(f"    merged - {preamble_obj}")

        # Now processing preamble rows
        logger.debug(f"  preamble for {ws_name!r}")
        for row in ws[RowType.PREAMBLE]:
            try:
                # process this property
                new_files = _process_property(
                    row.values[0],
                    row.values[1],
                    key_lu=template.key_lu,
                    data_obj=preamble_obj,
                    format_context=preamble_context,
                    root_obj=root_ct_obj,
                    data_obj_pointer=template_root_obj_pointer
                    + preamble_object_pointer,
                )
                # TODO we might want to use copy+preamble_merger here too,
                # to for complex properties that require mergeStrategy

                if new_files:
                    collected_files.extend(new_files)
            except ParsingException as e:
                errors_so_far.append(e)

        # Now pushing it up / merging with the whole thing
        copy_of_template_root = {}
        _set_val(preamble_object_pointer, preamble_obj, copy_of_template_root)
        logger.debug("merging root objs")
        logger.debug(f" {template_root_obj}")
        logger.debug(f" {copy_of_template_root}")
        template_root_obj = root_ct_merger.merge(
            template_root_obj, copy_of_template_root
        )
        logger.debug(f"  merged - {template_root_obj}")

    if template_root_obj_pointer != "":
        _set_val(template_root_obj_pointer, template_root_obj, root_ct_obj)
    else:
        root_ct_obj = template_root_obj

    return root_ct_obj, collected_files, errors_so_far
