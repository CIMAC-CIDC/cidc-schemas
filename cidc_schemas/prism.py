import re
import json
import os
import copy
import uuid
from typing import Union, BinaryIO
import jsonschema
from deepdiff import grep
import datetime
from jsonmerge import merge, Merger, exceptions as jsonmerge_exceptions
from collections import namedtuple
from jsonpointer import JsonPointer, JsonPointerException, resolve_pointer, EndOfList

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from cidc_schemas.constants import SCHEMA_DIR, TEMPLATE_DIR


def _set_val(
        pointer: str, 
        val: object, 
        context: dict, 
        root: Union[dict, None] = None, 
        context_pointer: Union[str, None] = None, 
        verb=False):
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
        verb: indicates if debug logic should be printed.

    Returns:
       Nothing
    """

    # special case to set context doc itself
    if pointer.rstrip('#') == '':
        context.update(val)
        return


    #fill defaults 
    if root is None:
        root = context
    if context_pointer is None:
        context_pointer = "/"
    

    # first we need to convert pointer to an absolute one
    # if it was a relative one (https://tools.ietf.org/id/draft-handrews-relative-json-pointer-00.html)
    if pointer.startswith('/'):
        jpoint = JsonPointer(pointer)
        doc = context

    else:
        # parse "relative" jumps up
        jumpups, slash, rem_pointer = pointer.partition('/')
        try:
            jumpups = int(jumpups.rstrip('#'))
        except ValueError:
            jumpups = 0

        # check that we don't have to jump up more than we dived in already 
        assert jumpups <= context_pointer.rstrip('/').count('/'), \
            f"Can't set value for pointer {pointer} to many jumps up from current context."

        # and we'll go down remaining part of `pointer` from there
        jpoint = JsonPointer(slash+rem_pointer)
        if jumpups > 0:
            # new context pointer 
            higher_context_pointer = '/'.join(context_pointer.strip('/').split('/')[:-1*jumpups])
            # making jumps up, by going down context_pointer but no all the way down
            if higher_context_pointer == '':
                doc = root
                assert len(jpoint.parts) > 0, f"Can't update root object (pointer {pointer})"
            else: 
                doc = resolve_pointer(root, '/'+higher_context_pointer)
        else:
            doc = context


    # then we update it
    for i, part in enumerate(jpoint.parts[:-1]):

        try:
            doc = jpoint.walk(doc, part)

        except (JsonPointerException, IndexError) as e:
            # means that there isn't needed sub-object in place, so create one

            # look ahead to figure out a proper type that needs to be created
            next_thing = __jpointer_get_next_thing(jpoint.parts[i+1])
            
            # insert it
            __jpointer_insert_next_thing(doc, jpoint, part, next_thing)

            # and `walk` it again - this time should be OK
            doc = jpoint.walk(doc, part)


        if isinstance(doc, EndOfList):
            actual_doc = __jpointer_get_next_thing(jpoint.parts[i+1])
            __jpointer_insert_next_thing(doc.list_, jpoint, "-", actual_doc)
            doc = actual_doc

    __jpointer_insert_next_thing(doc, jpoint, jpoint.parts[-1], val)


def  __jpointer_get_next_thing(next_part) -> Union[dict, list]:
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


def  __jpointer_insert_next_thing(doc, jpoint, part, next_thing):
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
            doc[typed_part] = next_thing

        # if doc is an empty array we hit an error when we try to paste to [0] index,
        # so just append
        except IndexError:
            doc.append(next_thing)


def _get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field:
            fields_found.append(value)

        elif isinstance(value, dict):
            results = _get_recursively(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = _get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)

    return fields_found


LocalFileUploadEntry = namedtuple('LocalFileUploadEntry', ["local_path", "gs_key", "upload_placeholder"])

def _process_property(
        key: str,
        raw_val,
        assay_hint: str,
        key_lu: dict,
        data_obj: dict,
        format_context: dict,
        root_obj: Union[None, dict] = None,
        data_obj_pointer: Union[None, str] = None,
        verb: bool = False) -> LocalFileUploadEntry:
    """
    Takes a single property (key, val) from spreadsheet, determines
    where it needs to go in the final object, then inserts it.

    Args:
        key: property name,
        raw_val: value of a property beeing processed,
        assay_hint: 'wes' or similar to create proper urls
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
        verb: boolean indicating verbosity

    Returns:
        LocalFileUploadEntry(
            local_path = "/local/file/from/excel/file/cell",   
            gs_key = "constructed/GCS/path/where/this/artifact/shold/endup",
            upload_placeholder = 'uuiduuiduuid-uuid-uuid-uuiduuid' # unique artifact/upload_placeholder
        )

    """

    if verb:
        print(f"processing property {key!r} - {raw_val!r}")
    # coerce value
    field_def = key_lu[key.lower()]
    if verb:
        print(f'found def {field_def}')
    
    val = field_def['coerce'](raw_val)

    # or set/update value in-place in data_obj dictionary 
    pointer = field_def['merge_pointer']
    if field_def.get('is_artifact'):
        pointer+='/upload_placeholder'

    _set_val(pointer, val, data_obj, root_obj, data_obj_pointer, verb=verb)

    if verb:
        print(f'current {data_obj}')
        print(f'current root {root_obj}')

    if field_def.get('is_artifact'):

        if verb:
            print(f'collecting local_file_path {field_def}')

        gs_key = field_def['gcs_uri_format'].format_map(format_context)

        return LocalFileUploadEntry(
            local_path = raw_val,
            gs_key = gs_key,
            # for artifacts `val` is a uuid
            upload_placeholder = val
        )
    

SUPPORTED_ASSAYS = ["wes", "olink"]
SUPPORTED_MANIFESTS = ["pbmc"]
SUPPORTED_TEMPLATES = SUPPORTED_ASSAYS + SUPPORTED_MANIFESTS
def prismify(xlsx_path: Union[str, BinaryIO], template_path: str, assay_hint: str, verb: bool = False) -> (dict, dict):
    """
    Converts excel file to json object. It also identifies local files
    which need to uploaded to a google bucket and provides some logic
    to help build the bucket url.

    e.g. file list
    [
        {
            'local_path': '/path/to/fwd.fastq',
            'gs_key': '10021/Patient_1/sample_1/aliquot_1/wes_forward.fastq'
        }
    ]


    Args:
        xlsx_path: file on file system to excel file or the open file itself
        template_path: path on file system relative to schema root of the
                        temaplate

        assay_hint: string used to help idnetify properties in template. Must
                    be the the root of the template filename i.e.
                    wes_template.json would be wes.
        verb: boolean indicating verbosity

    Returns:
        (tuple):
            arg1: clinical trial object with data parsed from spreadsheet
            arg2: list of LocalFileUploadEntry'es that describe each file identified:
                LocalFileUploadEntry(
                    local_path = "/local/path/to/a/data/file/parsed/from/template",
                    gs_key = "constructed/relative/to/clinical/trial/GCS/path",
                    upload_placeholder = "random_uuid-for-artifact-upload"
                )

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
    With exception - "3/lead_organization_study_id" which says basically 
    "go 3 levels up in the hierarchy and take lead_org_study_id field". 

    E.g. WES:
        {
          "lead_organization_study_id": "4412" # from `3/lead_organization_study_id`
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
                    "cimac_aliquot_id": ...         # from "0/cimac_aliquot_id", 
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

    # data rows will require a unique identifier
    if assay_hint not in SUPPORTED_TEMPLATES:
        raise NotImplementedError(f'{assay_hint} is not supported yet, only {SUPPORTED_TEMPLATES} are supported.')

    
    # get the root CT schema
    root_ct_schema = load_and_validate_schema("clinical_trial.json")
    # create the result CT dictionary
    root_ct_obj = {"_root_ct_obj": assay_hint} if verb else {}
    # and merger for it
    # and where to collect all local file refs
    collected_files = []

    # read the excel file
    xslx = XlTemplateReader.from_excel(xlsx_path)
    # get corr xsls schema
    xlsx_template = Template.from_json(template_path)
    xslx.validate(xlsx_template)

    # loop over spreadsheet worksheets
    for ws_name, ws in xslx.grouped_rows.items():
        if verb:
            print(f'next worksheet {ws_name}')

        # Here we take only first two cells from preamble as key and value respectfully,
        # lowering keys to match template schema definitions.
        preamble_context = dict((r[0].lower(), r[1]) for r in ws.get(RowType.PREAMBLE, []))
        # We need this full "preamble dict" (all key-value pairs) prior to processing
        # properties from data_columns or preamble wrt template schema definitions, because 
        # there can be a 'gcs_uri_format' that needs to have access to all values.

        templ_ws = xlsx_template.schema['properties']['worksheets'][ws_name]
        preamble_object_schema = load_and_validate_schema(templ_ws['prism_preamble_object_schema'])
        preamble_merger = Merger(preamble_object_schema)
        preamble_object_pointer = templ_ws['prism_preamble_object_pointer']
        data_object_pointer = templ_ws['prism_data_object_pointer']

        # creating preamble obj 
        preamble_obj = {"_preamble_obj": f"{assay_hint}:{ws_name}"} if verb else {}
        
        data = ws[RowType.DATA]
        if data:
            # get the data
            headers = ws[RowType.HEADER][0]

            # for row in data:
            for i, row in enumerate(data):

                if verb:
                    print(f'next data row {i} {row}')

                # creating data obj 
                data_obj = {"_data_obj": f"{assay_hint}:{ws_name}:row_{i}"} if verb else {}
                copy_of_preamble = {"_preamble_obj": f"copy_for:{assay_hint}:{ws_name}:row_{i}"} if verb else {}
                _set_val(data_object_pointer, data_obj, copy_of_preamble, root_ct_obj, preamble_object_pointer, verb=verb)

                # We create this "data record dict" (all key-value pairs) prior to processing
                # properties from data_columns wrt template schema definitions, because 
                # there can be a 'gcs_uri_format' that needs to have access to all values.
                local_context = dict(zip([h.lower() for h in headers], row))

                # create dictionary per row
                for key, val in zip(headers, row):
                    
                    # get corr xsls schema type 
                    new_file = _process_property(
                        key, val,
                        assay_hint=assay_hint,
                        key_lu=xlsx_template.key_lu,
                        data_obj=data_obj,
                        format_context=dict(local_context, **preamble_context), # combine contextes
                        root_obj=copy_of_preamble,
                        data_obj_pointer=data_object_pointer,
                        verb=verb)
                    if new_file:
                        collected_files.append(new_file)

                if verb:
                    print('merging preambles')
                    print(f'   {preamble_obj}')
                    print(f'   {copy_of_preamble}')
                preamble_obj = preamble_merger.merge(preamble_obj, copy_of_preamble)
                if verb:
                    print(f'merged - {preamble_obj}')

        _set_val(preamble_object_pointer, preamble_obj, root_ct_obj, verb=verb)
        

        for row in ws[RowType.PREAMBLE]:
            # process this property
            new_file = _process_property(
                row[0], row[1], 
                assay_hint=assay_hint, 
                key_lu=xlsx_template.key_lu, 
                data_obj=preamble_obj, 
                format_context=preamble_context, 
                root_obj=root_ct_obj, 
                data_obj_pointer=preamble_object_pointer, 
                verb=verb)
            # TODO we might want to use copy+preamble_merger here too,
            # to for complex properites that require mergeStrategy 
            
            if new_file:
                collected_files.append(new_file)

    # return root object and files list
    return root_ct_obj, collected_files


def _get_path(ct: dict, key: str) -> str:
    """
    find the path to the given key in the dictionary

    Args:
        ct: clinical_trial object to be modified
        key: the identifier we are looking for in the dictionary

    Returns:
        arg1: string describing the location of the key
    """

    # first look for key as is
    ds1 = ct | grep(key, match_string=True)
    count1 = 0
    if 'matched_values' in ds1:
        count1 = len(ds1['matched_values'])

    # the hack fails if both work... probably need to deal with this
    if count1 == 0:
        raise KeyError(f"key: {key} not found")

    # get the keypath
    return ds1['matched_values'].pop()


def _get_source(ct: dict, key: str, skip_last=None) -> dict:
    """
    extract the object in the dicitionary specified by
    the supplied key (or one of its parents.)

    Args:
        ct: clinical_trial object to be searched
        key: the identifier we are looking for in the dictionary,
        skip_last: how many levels at the end of key path we want to skip.

    Returns:
        arg1: string describing the location of the key
    """

    # tokenize.
    key = key.replace("root", "").replace("'", "")
    tokens = re.findall(r"\[(.*?)\]", key)

    if skip_last:
        tokens = tokens[0:-1*skip_last]
    
    # keep getting based on the key.
    cur_obj = ct
    for token in tokens:
        try:
            token = int(token)
        except ValueError:
            pass

        cur_obj = cur_obj[token]

    return cur_obj



def _set_data_format(ct: dict, artifact: dict):
    """
    Discover the correct data format for the given artifact.

    Args:
        ct: a clinical trial object with artifact inserted
        artifact: a reference to the artifact object inserted in `ct`.

        NOTE: in-place updates to artifact must trigger in-place updates to `ct`.
    """
    # This is invalid for all artifact types, and will
    # deliberately trigger a validation error below.
    artifact['data_format'] = '[NOT SET]'

    validator: jsonschema.Draft7Validator = load_and_validate_schema(
        'clinical_trial.json', return_validator=True)
    try:
        validator.validate(ct)
    except jsonschema.exceptions.ValidationError as e:
        # Since data_format is specified as a constant in the schema,
        # the validator_value on this exception will be the desired data format.
        artifact['data_format'] = e.validator_value

def merge_artifact(
    ct: dict,
    assay_type: str,
    artifact_uuid: str,
    object_url: str,
    file_size_bytes: int,
    uploaded_timestamp: str,
    md5_hash: str
) -> (dict, dict):
    """
    create and merge an artifact into the metadata blob
    for a clinical trial. The merging process is automatically
    determined by inspecting the gs url path.

    Args:
        ct: clinical_trial object to be searched
        object_url: the gs url pointing to the object being added
        file_size_bytes: integer specifying the number of bytes in the file
        uploaded_timestamp: time stamp associated with this object
        md5_hash: hash of the uploaded object, usually provided by
                    object storage

    """ 

    # urls are created like this in _process_property:
    file_name, uuid = object_url.split("/")[-2:]


    artifact = {
        # TODO 1. this artifact_category should be filled out during prismify
        "artifact_category": "Assay Artifact from CIMAC",
        "object_url": object_url,
        "file_name": file_name,
        "file_size_bytes": file_size_bytes,
        "md5_hash": md5_hash,
        "uploaded_timestamp": uploaded_timestamp
    }

    # We're using uuids to find path in CT where corresponding artifact is located
    # As uuids are unique, this should be fine.
    uuid_field_path = _get_path(ct, artifact_uuid)

    # As "uuid_field_path" contains path to a field with uuid,
    # we're looking for an artifact that contains it, not the "string" field itself
    # That's why we need skip_last=1, to get 1 "level" higher 
    # from 'uuid_field_path' field to it's parent - existing_artifact obj. 
    existing_artifact = _get_source(ct, uuid_field_path, skip_last=1)

    ## TODO this might be better like this - with merger:
    # artifact_schema = load_and_validate_schema(f"artifacts/{artifact_type}.json")
    # artifact_parent[file_name] = Merger(artifact_schema).merge(existing_artifact, artifact)
    # TODO but for now like this
    existing_artifact.update(artifact)

    _set_data_format(ct, existing_artifact)

    # return new object and the artifact that was merged
    return ct, existing_artifact

class InvalidMergeTargetException(ValueError):
    """Exception raised for target of merge_clinical_trial_metadata being non schema compliant."""

def merge_clinical_trial_metadata(patch: dict, target: dict) -> dict:
    """
    merges two clinical trial metadata objects together

    Args:
        patch: the metadata object to add
        target: the existing metadata object

    Returns:
        arg1: the merged metadata object
    """

    # merge the copy with the original.
    validator = load_and_validate_schema(
        "clinical_trial.json", return_validator=True)
    schema = validator.schema

    # first we assert original object is valid
    try:
        validator.validate(target)
    except jsonschema.ValidationError as e:
        raise InvalidMergeTargetException(f"Merge target is invalid: {target}") from e

    # next assert the un-mutable fields are equal
    # these fields are required in the schema
    # so previous validation assert they exist
    key_details = ["lead_organization_study_id"]
    for d in key_details:
        if patch.get(d) != target.get(d):
            raise RuntimeError("unable to merge trials with different \
                lead_organization_study_id")

    # merge the two documents
    merger = Merger(schema)
    merged = merger.merge(target, patch)

    # validate this
    validator.validate(merged)

    # now return it
    return merged
