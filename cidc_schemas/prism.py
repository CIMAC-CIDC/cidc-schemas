import re
import json
import os
import copy
import jsonschema
from deepdiff import grep
import datetime
from jsonmerge import merge, Merger
from collections import namedtuple
from jsonpointer import JsonPointer, JsonPointerException

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from cidc_schemas.constants import SCHEMA_DIR, TEMPLATE_DIR


def _get_coerce(ref: str):
    """
    This function takes a jscon-schema style $ref pointer,
    opens the schema and determines the best python
    function to type the value.

    Args:
        ref: /path/to/schema.json

    Returns:
        Python function pointer
    """

    referer = {'$ref': ref}

    resolver_cache = {}
    while '$ref' in referer:
        # get the entry
        resolver = jsonschema.RefResolver(
            f'file://{SCHEMA_DIR}/schemas', referer, resolver_cache)
        _, referer = resolver.resolve(referer['$ref'])

    entry = referer
    # add our own type conversion
    t = entry['type']
    if t == 'string':
        return str
    elif t == 'integer':
        return int
    elif t == 'number':
        return float
    else:
        raise NotImplementedError(f"no coercion available for type:{t}")


def _load_keylookup(template_path: str) -> dict:
    """
    The excel spreadsheet use a human friendly (no _) name
    for properties, where the field it refers to in the schema
    has a different name. This function builds a dictionary
    to lookup these differences.

    It also populates the coercion function for each
    property.

    Args:
        template_path: /path/to/template.json

    Returns:
        Dictionary keyed by spreadsheet property names
    """

    # get the template.
    with open(template_path) as fin:
        t = json.load(fin)

    # create a key lookup dictionary
    key_lu = {}

    # checks if we have a cast func for that 'type_ref'
    def _add_coerce(field_def:dict) -> dict: 
        if 'load_through' in field_def:
            return dict(coerce=_get_coerce(field_def['load_through']), **field_def)
        else: 
            return dict(coerce=_get_coerce(field_def['type_ref']), **field_def)

    # loop over each worksheet
    worksheets = t['properties']['worksheets']
    for worksheet in worksheets:

        # loop over each row in pre-amble
        pre_rows = worksheets[worksheet]['preamble_rows']
        for preamble_key, preamble_def in pre_rows.items():

            # populate lookup
            key_lu[preamble_key] = _add_coerce(preamble_def)
            # we expect preamble_def from `_template.json` have 3 fields (as for template.schema)
            # "merge_pointer" "type_ref" "load_through"

        # load the data columns
        dat_cols = worksheets[worksheet]['data_columns']
        for section_key, section in dat_cols.items():
            for column_key, column_def in section.items():

                # populate lookup
                key_lu[column_key] = _add_coerce(column_def)
                # we expect column_def from `_template.json` have 3 fields (as for template.schema)
                # "merge_pointer" "type_ref" "load_through"


    # # special case for wes keys.
    # if 'wes' in template_path:
    #     ref = "assays/components/ngs/ngs_assay_record.json#properties/cimac_aliquot_id"
    #     data_key = "cimac_aliquot_id"
    #     populate_lu(ref, key_lu, data_key)

    return key_lu



def _set_val(pointer: str, val: object, trial: dict, verbose=False):
    """
    This function given a *pointer* (jsonpointer, RFC 6901)
    to a property in a python object, sets the supplied value
    inplace in the *trial* object.

    The object we are adding data to is *trial*. The object
    may or maynot have any of the intermediate structure
    to fully insert the desired property.

    For example: consider trial = {}
    And pointer = "/participants/0/prop1"
    
    We should assume to update sub-object: 
        {
            "participants": ...
        }
    Lets truncate the path to exclude tokens we've already
    consumed:

    path = "0/prop1"

    Next we see an `0` property which in json-pointer
    denotes a first element of an array. So the implication
    is that the value of 'participants' is list.
        {
            "participants": [...]
        }

    Truncated again path = "prop1"

    We see it's a string, not an integer so we know 
    we are entering an object with *prop1* as a property. 
    This is the final piece of the *path* so we can assign the val:
        {
            "participants": [{
                "prop1": val
            }]
        }


    *One limitation* of this code is that no list can have
    more than 1 item. This is likely OK because we are building
    one object per record in the excel templates and using
    a seperate library to merge objects.

    Args:
        pointer: jsonpointer path to the property being set
        val: the value being set
        trial: the python object being constructed
        verbose: indicates if debug logic should be printed.

    Returns:
       Nothing
    """

    jpoint = JsonPointer(pointer)

    assert len(jpoint.parts) > 0, "Can't update root object"


    # we need to walk our trial doc up until the last step
    doc = trial
    # then we update it
    for i, part in enumerate(jpoint.parts[:-1]):

        try:
            doc = jpoint.walk(doc, part)

        except (JsonPointerException, IndexError) as e:
            # means that we probably don't have needed sub-object in place
            # so we need to create one

            # but we need to look ahead to figure out
            # a proper type that need to be created
            if i+1 == len(jpoint.parts):
                raise NotImplementedError(f'no next_part in jsonpointer{pointer}')

            next_part = jpoint.parts[i+1]
            
            typed_part = jpoint.get_part(doc, part)
            # `part` looks like array index, so create array
            if jpoint._RE_ARRAY_INDEX.match(str(next_part)):
                insert = []
            # or just dict as default
            else:
                insert = {}
            try:
                doc[typed_part] = insert
            except IndexError:
                doc.append(insert)

            # now we `walk` it again - this time should be ok
            doc = jpoint.walk(doc, part)

    # now we update it
    doc[jpoint.parts[-1]] = val

    return trial


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


def _process_property(
        row: list,
        key_lu: dict,
        schema: dict,
        data_obj: dict,
        assay_hint: str,
        verb: bool) -> dict:
    """
    Takes a single property (key, val) from spreadsheet, determines
    where it needs to go in the final object, then inserts it.

    Args:
        row: array with two fields, key-val
        key_lu: dictionary to translate from template naming to json-schema
                property names
        data_object: dictionary we are building to represent data
        assay_hint: assay pre-fixed used to help identify property in schema
        verb: boolean indicating verbosity

    Returns:
        TBD

    """

    # simplify
    key = row[0]
    raw_val = row[1]

    if verb:
        print(f"processing {key!r} {raw_val!r}")
    # coerce value
    field_def = key_lu[key.lower()]
    if verb:
        print(f'found def {field_def}')
    
    val = field_def['coerce'](raw_val)
    if verb:
        print(f'coerced {raw_val!r} - {val!r}')
    
    # don't try to get file_path, this needs to be resolved later
    if field_def.get('load_through') == 'assays/components/local_file.json#properties/file_path':

        # setup the base path
        gs_key = _get_recursively(data_obj, "lead_organization_study_id")[0]
        gs_key = f'{gs_key}/{_get_recursively(data_obj, "cimac_participant_id")[0]}'
        gs_key = f'{gs_key}/{_get_recursively(data_obj, "cimac_sample_id")[0]}'
        gs_key = f'{gs_key}/{_get_recursively(data_obj, "cimac_aliquot_id")[0]}'
        gs_key = f'{gs_key}/{assay_hint}'
        #gs_key = gs_key.replace(" ", "_")

        # do the suffix
        tmp = key.lower().split(" ")

        # bespoke suffix logic.
        just_use = set(["fastq"])
        text_use = set(["group"])
        if tmp[1] in just_use:
            suffix = f'{tmp[0]}.{tmp[1]}'
        elif tmp[1] in text_use:
            suffix = f'{tmp[0]}_{tmp[1]}.txt'
        gs_key = f'{gs_key}_{suffix}'

        # return local_path entry
        return {
            "template_key": key,
            "local_path": val,
            "field_def": field_def,
            "gs_key": gs_key
        }

    # or set/update value in-place in data_obj dictionary 
    _set_val(field_def['merge_pointer'], val, data_obj, verbose=verb)

    if verb:
        print(f'current {data_obj}')
    

def prismify(xlsx_path: str, template_path: str, assay_hint: str = "", verb: bool = True) -> (dict, dict):
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
        xlsx_path: file on file system to excel file.
        template_path: path on file system relative to schema root of the
                        temaplate

        assay_hint: string used to help idnetify properties in template. Must
                    be the the root of the template filename i.e.
                    wes_template.json would be wes.
        verb: boolean indicating verbosity

    Returns:
        (tuple):
            arg1: clinical trial object with data parsed from spreadsheet
            arg2: list of objects which describe each file identified.
    """

    # get the schema and validator
    validator = load_and_validate_schema(
        "clinical_trial.json", return_validator=True)
    schema = validator.schema

    # this lets us lookup xlsx-to-schema keys
    key_lu = _load_keylookup(template_path)

    local_file_paths = []

    # read the excel file
    t = XlTemplateReader.from_excel(xlsx_path)

    # create the root dictionary.
    root = {}
    data_rows = []

    # loop over spreadsheet worksheets
    for ws in t.grouped_rows.values():

        # Compare preamble rows
        for row in ws[RowType.PREAMBLE]:

            # process this property
            local_file_paths.append(_process_property(row, key_lu, schema, root, assay_hint, verb))

        # move to headers
        headers = ws[RowType.HEADER][0]

        # track these identifiers
        potential_ids = {
            "CIMAC PARTICIPANT ID": "",
            "CIMAC SAMPLE ID": "",
            "CIMAC ALIQUOT ID": ""
        }

        # get the data.
        data = ws[RowType.DATA]
        for row in data:

            # create dictionary per row
            curd = copy.deepcopy(root)
            for key, val in zip(headers, row):

                # process this property
                local_file_paths.append(_process_property([key, val], key_lu, schema, curd, assay_hint, verb))

                # track ids
                if key in potential_ids:
                    potential_ids[key] = val

            # save the entry
            data_rows.append(curd)

            # data rows will require a unique identifier
            if assay_hint == "wes":

                # # create a unique key
                # unique_key = potential_ids['CIMAC PARTICIPANT ID']
                # unique_key = f'{unique_key}_{potential_ids["CIMAC SAMPLE ID"]}'
                # unique_key = f'{unique_key}_{potential_ids["CIMAC ALIQUOT ID"]}'

                # # add this to the most recent payload
                # _process_property(['cimac_aliquot_id', unique_key], key_lu, schema,
                #         curd, assay_hint, verb)
                pass
            else:
                raise NotImplementedError(f'only WES is supported, please add additional support \
                    for {assay_hint}')

    # create the merger
    merger = Merger(schema)

    # iteratively merge.
    cur_obj = data_rows[0]
    for i in range(1, len(data_rows)):
        cur_obj = merger.merge(cur_obj, data_rows[i])

    # return the object.
    return cur_obj, local_file_paths


def _deep_get(obj: dict, key: str):
    """
    returns value of they supplied key
    gotten via deepdif
    """

    # tokenize.
    key = key.replace("root", "").replace("'", "")
    tokens = re.findall(r"\[(.*?)\]", key)

    # keep getting based on the key.
    cur_obj = obj
    for token in tokens:
        cur_obj = cur_obj[token]

    return cur_obj, tokens[-2]


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
        raise NotImplementedError(f"key: {key} not found in dictionary")

    # get the keypath
    return ds1['matched_values'].pop()


def _get_source(ct: dict, key: str, level="sample") -> dict:
    """
    extract the object in the dicitionary specified by
    the supplied key (or one of its parents.)

    Args:
        ct: clinical_trial object to be searched
        key: the identifier we are looking for in the dictionary,
        level: a keyword describing which level in the key path
                (trial, participants, sample, aliquot) we want to return

    Returns:
        arg1: string describing the location of the key
    """

    # tokenize.
    key = key.replace("root", "").replace("'", "")
    tokens = re.findall(r"\[(.*?)\]", key)

    # this will get us to the object we have the key for
    if level == "sample":
        tokens = tokens[0:-3]
    elif level == "aliquot":
        tokens = tokens[0:-1]
    else:
        raise NotImplementedError(
            f'the following level is not supported: {level}')

    # keep getting based on the key.
    cur_obj = ct
    for token in tokens:
        try:
            token = int(token)
        except ValueError:
            pass

        cur_obj = cur_obj[token]

    return cur_obj


def _merge_artifact_wes(
    ct: dict,
    object_url: str,
    file_size_bytes: int,
    uploaded_timestamp: str,
    md5_hash: str
):
    """
    create and merge an artifact into the WES assay metadata.
    The artifacts currently supported are only the input
    fastq files and read mapping group file.

    Args:
        ct: clinical_trial object to be searched
        object_url: the gs url pointing to the object being added
        file_size_bytes: integer specifying the numebr of bytes in the file
        uploaded_timestamp: time stamp associated with this object
        md5_hash: hash of the uploaded object, usually provided by
                    object storage

    """

    # replace gs prfix if exists.
    object_url, lead_organization_study_id, \
        cimac_participant_id, cimac_sample_id, cimac_aliquot_id, \
        file_name = _split_objurl(object_url)

    # get the genomic source.
    keypath = _get_path(ct, cimac_aliquot_id)
    sample_obj = _get_source(ct, keypath)
    genomic_source = sample_obj['genomic_source']

    # create the artifact.
    artifact = {
        "artifact_category": "Assay Artifact from CIMAC",
        "object_url": object_url,
        "file_name": file_name,
        "file_size_bytes": 1,
        "md5_hash": md5_hash,
        "uploaded_timestamp": datetime.datetime.now().strftime('%Y-%M-%dT%H:%m:%S')
    }

    # create the wes input object which will be added to existing data
    obj = {}

    # check if we are adding read group mapping file.
    if "wes_read_group" in file_name:

        # set the artifact type and save
        artifact["file_type"] = "Other"
        obj['read_group_mapping_file'] = artifact

    else:

        # set the artifact type
        artifact["file_type"] = "FASTQ"

        # # determine how to craft the artifact
        # obj[genomic_source] = {}
        # if "wes_forward" in file_name:
        #     obj[genomic_source]['fastq_1'] = artifact

        # elif "wes_reverse" in file_name:
        #     obj[genomic_source]['fastq_2'] = artifact

    # copy the metadata and add this a new record.
    # note this will clobber whatever is here. This is
    # OK because the original copy of ct will have the
    # clobbered data, while the new copy will have
    # the new entry which will get appended to the
    # "records" list by the merge by ID strategy
    # specified in the json-schema for records
    ct_copy = copy.deepcopy(ct)
    aliquot_obj = _get_source(ct_copy, keypath, level="aliquot")
    ct_copy['assays']['wes'][0]['records'][0]['files'] = obj

    # merge the copy with the original.
    validator = load_and_validate_schema(
        "clinical_trial.json", return_validator=True)
    schema = validator.schema
    merger = Merger(schema)

    ct_new = merger.merge(ct, ct_copy)

    # validate the new data
    validator.validate(ct_new)

    # return the new dictionary
    return ct_new


def _split_objurl(obj_url: str) -> (str, str, str, str, str, str):
    """
    splits gs_url into components and returns them

    Args:
        obj_url: gs://url/to/file

    Returns:
        arg1: tuple of the components
    """

    # replace gs prfix if exists.
    obj_url = obj_url.replace("gs://", "")

    # parse the url to get key identifiers
    tokens = obj_url.split("/")
    lead_organization_study_id = tokens[0]
    cimac_participant_id = tokens[1]
    cimac_sample_id = tokens[2]
    cimac_aliquot_id = tokens[3]
    file_name = tokens[4]

    return obj_url, lead_organization_study_id, cimac_participant_id, \
        cimac_sample_id, cimac_aliquot_id, file_name


def merge_artifact(
    ct: dict,
    object_url: str,
    file_size_bytes: int,
    uploaded_timestamp: str,
    md5_hash: str
):
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

    # replace gs prfix if exists.
    object_url, lead_organization_study_id, \
        cimac_participant_id, cimac_sample_id, cimac_aliquot_id, \
        file_name = _split_objurl(object_url)

    # define criteria.
    wes_names = {'wes_forward', 'wes_reverse', 'wes_read_group'}

    # test criteria.
    if any(wes_name in file_name for wes_name in wes_names):
        new_ct = _merge_artifact_wes(
            ct,
            object_url,
            file_size_bytes,
            uploaded_timestamp,
            md5_hash
        )
    else:
        raise NotImplementedError(
            f'the following file_name is not supported: {file_name}')

    # return new object
    return new_ct
