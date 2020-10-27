"""Build metadata dictionaries from Excel files."""
import json
import logging
import base64
import hmac
from collections import defaultdict
from typing import Any, List, NamedTuple, Tuple, Union, Optional, Dict

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import (
    Template,
    AtomicChange,
    LocalFileUploadEntry,
    ParsingException,
)
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.template_writer import RowType
from cidc_schemas.constants import SCHEMA_DIR
from .merger import PRISM_MERGE_STRATEGIES, MergeCollisionException
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


def _apply_changes(
    changes: List[AtomicChange],
    data_obj: dict,
    root_obj: Union[None, dict] = None,
    data_obj_pointer: Union[None, str] = None,
):
    """
    Takes a list of AtomicChanges and applies it to the `data_obj` within 
        root_obj: root dictionary we are building to represent data,
                  that holds 'data_obj' within 'data_obj_pointer'
        data_obj_pointer: pointer of 'data_obj' within 'root_obj'.
                          this will allow to process relative json-pointer properties
                          to jump out of data_object
    """

    for ch in changes:
        _set_val(ch.pointer, ch.value, data_obj, root_obj, data_obj_pointer)


_encrypt_hmac = None


def set_prism_encrypt_key(key):
    global _encrypt_hmac
    if _encrypt_hmac != None:
        raise Exception("attempt to set_prism_encrypt_key twice")

    _encrypt_hmac = hmac.new(str(key).encode(), digestmod="SHA512")


def _get_encrypt_hmac():
    return _encrypt_hmac.copy()


def _check_encrypt_init():
    if not _encrypt_hmac:
        raise Exception("Encrypt is not initialized")


_ENCRYPTED_FIELD_LEN = 32


def _encrypt(obj):
    _check_encrypt_init()

    h = _get_encrypt_hmac()
    h.update(str(obj).encode())
    return (base64.b64encode(h.digest()))[:_ENCRYPTED_FIELD_LEN].decode()


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
            arg2: list of `LocalFileUploadEntry`s that describe each file identified:
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

    _check_encrypt_init()

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
    root_ct_merger = Merger(root_ct_schema, strategies=PRISM_MERGE_STRATEGIES)
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
            preamble_object_schema, strategies=PRISM_MERGE_STRATEGIES
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

                    combined_context = dict(local_context, **preamble_context)
                    try:
                        changes, new_files = template.process_field_value(
                            ws_name, key, val, combined_context, _encrypt
                        )
                    except ParsingException as e:
                        errors_so_far.append(e)
                    else:
                        _apply_changes(
                            changes, data_obj, copy_of_preamble, data_object_pointer
                        )
                        collected_files.extend(new_files)

                try:
                    preamble_obj = preamble_merger.merge(preamble_obj, copy_of_preamble)
                except MergeCollisionException as e:
                    # Reformatting exception, because this mismatch happened within one template
                    # and not with some saved stuff.
                    wrapped = e.with_context(row=row.row_num, worksheet=ws_name)
                    errors_so_far.append(wrapped)
                    logger.info(f"MergeCollisionException: {wrapped}")

        # Now processing preamble rows
        logger.debug(f"  preamble for {ws_name!r}")
        for row in ws[RowType.PREAMBLE]:
            k, v, *_ = row.values
            try:
                changes, new_files = template.process_field_value(
                    ws_name, k, v, preamble_context, _encrypt
                )
            except ParsingException as e:
                errors_so_far.append(e)
            else:
                # TODO we might want to use copy+preamble_merger here too,
                # to for complex properties that require mergeStrategy
                _apply_changes(
                    changes,
                    preamble_obj,
                    root_ct_obj,
                    template_root_obj_pointer + preamble_object_pointer,
                )
                collected_files.extend(new_files)

        # Now pushing it up / merging with the whole thing
        copy_of_templ_root = {}
        _set_val(preamble_object_pointer, preamble_obj, copy_of_templ_root)
        logger.debug("merging root objs")
        logger.debug(f" {template_root_obj}")
        logger.debug(f" {copy_of_templ_root}")
        template_root_obj = root_ct_merger.merge(template_root_obj, copy_of_templ_root)
        logger.debug(f"  merged - {template_root_obj}")

    if template_root_obj_pointer != "":
        _set_val(template_root_obj_pointer, template_root_obj, root_ct_obj)
    else:
        root_ct_obj = template_root_obj

    return root_ct_obj, collected_files, errors_so_far
