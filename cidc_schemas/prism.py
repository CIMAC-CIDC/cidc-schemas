import re
import json
import os
import copy
import jsonschema
from deepdiff import grep
import datetime
from jsonmerge import merge, Merger

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from cidc_schemas.constants import SCHEMA_DIR, TEMPLATE_DIR


def _get_coerce(ref: str):
    """
    This function takes a jscon-schema style ref pointer,
    opens the schema and determines the best python
    function to type the value.

    Args:
        ref: /path/to/schema.json

    Returns:
        Python function pointer
    """

    # get the entry
    resolver = jsonschema.RefResolver(
        f'file://{SCHEMA_DIR}/schemas', {'$ref': ref})
    _, entry = resolver.resolve(ref)

    # add our own type conversion
    t = entry['type']
    if t == 'string':
        return str
    elif t == 'integer':
        return int
    elif t == 'number':
        return float
    else:
        raise NotImplementedError(f"no coercion available for type{t}")


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

    def populate_lu(ref: str, key_lu: dict, xlsx_key: str):
        # split on / because this lets us get the property name which
        # is at the end of the json-scehma reference.
        schema_key = ref.split("/")[-1]

        key_lu[xlsx_key] = {
            "schema_key": schema_key,
            "ref": ref,
            "coerce": _get_coerce(ref)
        }

    # loop over each worksheet
    worksheets = t['properties']['worksheets']
    for worksheet in worksheets:

        # loop over each row in pre-amble
        pre_rows = worksheets[worksheet]['preamble_rows']
        for xlsx_key in pre_rows.keys():

            # get the json reference used to define this property
            ref = pre_rows[xlsx_key]['$ref']

            # populate lookup
            populate_lu(ref, key_lu, xlsx_key)

        # load the data columns
        dat_cols = worksheets[worksheet]['data_columns']
        for section_key in dat_cols.keys():
            for data_key in dat_cols[section_key]:

                # get the json reference used to define this property
                ref = dat_cols[section_key][data_key]['$ref']

                # populate lookup.
                populate_lu(ref, key_lu, data_key)

    # special case for wes keys.
    if 'wes' in template_path:
        ref = "assays/components/ngs/ngs_entry.json#properties/entry_id"
        data_key = "entry_id"
        populate_lu(ref, key_lu, data_key)

    return key_lu


def _find_key(schema_key: str, schema: dict, assay_hint: str = "") -> str:
    """
    This finds a given json proptery in the resolved
    schema. It uses a library deepdif to recursively
    search the schema and it returns the path to that key as
    python notation string (i.e. array[0][key1][3][key2]).

    The search function can return multiple hits because an
    key can be in an object with mutliple level itself. Therefore
    I sort all the return hits and find the shortest one. The
    shortest path will be the first occurance of that key
    in the dictionary. In general we use this path as our
    choice.

    I've introduced the assay_hint string to help disambuguate
    a path to a key when there are multiple possibilities.
    Consider "assay_creator" a property in assay_core.json
    which is associated with every assay. Searching the schema
    for assay_creator will return multiple hits, the hint lets
    us prioritize which we are looking for.

    Args:
        schema_key: the property name we are looking for in the json-schema
        schema: the dictionary contain the whole clinical_trial schema
        assay_hint: optional string to help prioritize the path
          to they key, among equivalents.

    Returns:
        Path to the property searched for in python notation
    """

    # find key in the schema, this notation is
    # recommended usage of deepdif grep. assuming they
    # overload the pipe operator to simulate cmd line
    # grep
    ds = schema | grep(schema_key)
    if 'matched_paths' not in ds:
        raise KeyError('%s not found in schema' % schema_key)

    # sort potential matches, shortest is what we want.
    choices = sorted(ds['matched_paths'], key=len)

    # if there are equal length short matches, try to use assay hint
    choice = choices[0]
    if len(choices) > 1 and len(choices[0]) == len(choices[1]):
        if assay_hint != "":
            for i in range(len(choices)):
                if choices[i].count(assay_hint) > 0:
                    choice = choices[i]
                    break

    # return chosen one.
    return choice


def _set_val(path: str, val: object, trial: dict, verbose=False):
    """
    ** warning **
    This function is under active development and can likely be
    simplified/styled and will likely undergo change as more data
    are tested. Currently much of the debug logic is still
    in place while this matures. I suspect we can write this
    as a recursive function...

    The goal of this function is given a *path* to a property
    in a python object, set the supplied value. The path is
    a string representation of a propetry in a python object
    to be validated using clinical_trial json-schema.

    The object we are adding data to is *trial*. The object
    may or maynot have any of the intermediate structure
    to fully insert the desired property.

    For example: consider trial = {}
    And path = "['root']['properties']['participants']['items'][0]['properties']['prop1']"

    Here root is the special keyword for the first
    object in the string. Parameters allowed in a json object
    are defined in the 'properties' object of a json-schema.
    So by seeing properties we know we are entering an object
    and that 'participants' is a key in that object.
    object like so:
        {
            "participants": ...
        }
    Lets truncate the path to exclude tokens we've already
    consumed:

    path = "['items'][0]['properties']['prop1']"

    Next we see an 'item' property which in json-schema
    denotes an array. So the implication
    is that the value of 'participants' is list.
        {
            "participants": [...]
        }

    path = "['properties']['prop1']"

    Next we 'properties' so we know we are entering an object
    with *prop1* as a property. This is the
    final piece of the *path* so we can assign the val:
        {
            "participants": [{
                "prop1": val
            }]
        }


    The code below first tokenizes the string based on
    brackets.

    For each token we test for its json-schema modifier,
    'items', 'properties', 'allOf'. If we see items we need
    to add a list, assuming it doesn't exist, if we see properties
    we need to create a dictionary if it doesn't exist.

    *One limitation* of this code is that no list can have
    more than 1 item. This is likely OK because we are building
    one object per record in the excel templates and using
    a seperate library to merge objects.

    *Another caveat* is the 'allOf' modifier. When a schema
    is parsed it will treat 'allOf' as list of dictionaries
    like so:

    path = ['prop2']['allOf'][0]['properties'][...]

    For our purposes we need to treat the 'allOf' followed
    by the array entry and subsequent object properties
    as properties of the previous object 'prop2'. This
    is why there are "skip" blocks in the code which advance
    to the next token while keeping the pointer of the current
    object on 'prop2'.



    Args:
        path: the python path to the property being set
        val: the value being set
        trial: the python object being constructed
        verbose: indicates if debug logic should be printed.

    Returns:
       Nothing
    """

    # first we trim the root entry which is always the first dictionary
    # find by default returns the first occurance of the string
    stop = path.find("]") + 1
    path = path[stop::]

    # then we tokenize the paths.
    tmps = path.split("][")
    for i in range(len(tmps)):
        tmps[i] = tmps[i].replace("'", "")
        tmps[i] = tmps[i].replace("[", "")
        tmps[i] = tmps[i].replace("]", "")
    paths = tmps

    if verbose:
        print("-", paths)

    # modifier keys
    mods = set([
        "items",
        "properties"
    ])

    skipers = set([
        'allOf'
    ])

    # then we loop until we are done.
    curp = trial
    lenp = len(paths)
    skip_next = False
    for i in range(len(paths)):

        # simplify
        key = paths[i]

        if verbose:
            print("--", key)

        # short circuit
        if skip_next:
            skip_next = False
            if verbose:
                print("-skip-", key)
            continue

        # check if its final
        if i == lenp - 1:
            curp[key] = val

            if verbose:
                print("final", json.dumps(trial))
            return

        # check if this is a skiper
        elif key in skipers:
            if verbose:
                print("-skipers-", key)
            skip_next = True
            continue

        # check if this is a modifer
        elif key in mods:

            # we must be adding a new object.
            if key == "properties":
                if isinstance(curp, list):

                    # don't add new objects
                    if len(curp) == 0:
                        new_obj = {}
                        curp.append(new_obj)
                        curp = new_obj
                    else:
                        curp = curp[0]

                elif isinstance(curp, dict):
                    pass  # no need to do anything
                else:
                    raise NotImplementedError

        # not a modifer so add another level
        else:

            # is there already a key?
            if key not in curp:

                # look forward to see what we might add.
                key2 = paths[i+1]

                if verbose:
                    print("--2", key2)

                # its a list.
                if key2 == "items":
                    curp[key] = []

                # its a dictionary
                elif key2 == 'properties':
                    curp[key] = {}

                # also a dictionary, just will be preceeded by a nunber
                elif key2 == 'allOf':
                    # this assume allOf always creates object, maybe not true?
                    curp[key] = {}

                else:
                    raise NotImplementedError

            # set pointer for next round
            curp = curp[key]


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
        fp_lu: dict,
        verb: bool):
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
        None, data_obj is modified in place

    """
    # simplify
    key = row[0]
    val = row[1]

    # coerce value
    lu = key_lu[key.lower()]
    val = lu['coerce'](val)
    schema_key = lu['schema_key']

    # don't try to get file_path, this needs to be resolved later
    if schema_key == 'file_path':

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

        # create the entry.
        fp_lu['special'].append({
            "template_key": key,
            "local_path": val,
            "schema_ref": fp_lu[key],
            "gs_key": gs_key
        })

        # we still do nothing as this key isn't explicitly in the
        # data model. Another process will merge the artifact components
        # into this

        return

    # add to dictionary
    path = _find_key(schema_key, schema, assay_hint=assay_hint)
    _set_val(path, val, data_obj, verbose=verb)


def _build_fplu(assay_hint: str):

    # get the un resolved schema
    template_path = os.path.join(
        TEMPLATE_DIR, 'metadata', f'{assay_hint}_template.json')
    with open(template_path) as fin:
        schema = json.load(fin)

    # find key in the schema, this notation is
    # recommended usage of deepdif grep. assuming they
    # overload the pipe operator to simulate cmd line
    schema_key = 'artifact_link'
    ds = schema | grep(schema_key)
    if 'matched_paths' not in ds:
        raise KeyError(f'{schema_key} not found in schema')

    # sort potential matches, shortest is what we want.
    choices = sorted(ds['matched_paths'], key=len)

    # create tuples
    key_lu = {}
    for c in choices:

        # get the value and parent of the file link.
        val, pkey = _deep_get(schema, c)
        pkey = pkey.upper()
        key_lu[pkey] = val

    return key_lu


def prismify(xlsx_path: str, template_path: str, assay_hint: str = "", verb: bool = False) -> (dict, dict):
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

    # this helps us identify file paths in xlsx
    fp_lu = _build_fplu(assay_hint)

    # add a special key to track the files
    fp_lu['special'] = list()

    # read the excel file
    t = XlTemplateReader.from_excel(xlsx_path)

    # create the root dictionary.
    root = {}
    data_rows = []

    # loop over spreadsheet
    worksheet_names = t.grouped_rows.keys()
    for name in worksheet_names:

        # get the worksheat.
        ws = t.grouped_rows[name]

        # Compare preamble rows
        for row in ws[RowType.PREAMBLE]:

            # process this property
            _process_property(row, key_lu, schema, root,
                              assay_hint, fp_lu, verb)

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
                _process_property([key, val], key_lu, schema,
                                  curd, assay_hint, fp_lu, verb)

                # track ids
                if key in potential_ids:
                    potential_ids[key] = val

            # save the entry
            data_rows.append(curd)

            # data rows will require a unique identifier
            if assay_hint == "wes":

                # create a unique key
                unique_key = potential_ids['CIMAC PARTICIPANT ID']
                unique_key = f'{unique_key}_{potential_ids["CIMAC SAMPLE ID"]}'
                unique_key = f'{unique_key}_{potential_ids["CIMAC ALIQUOT ID"]}'

                # add this to the most recent payload
                _process_property(['entry_id', unique_key], key_lu, schema,
                        curd, assay_hint, fp_lu, verb)

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
    return cur_obj, fp_lu['special']


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
        "assay_category": "Whole Exome Sequencing (WES)",
        "object_url": object_url,
        "file_name": file_name,
        "file_size_bytes": 1,
        "md5_hash": md5_hash,
        "uploaded_timestamp": str(datetime.datetime.now()).split('.')[0]
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

        # determine how to craft the artifact
        obj[genomic_source] = {}
        if "wes_forward" in file_name:
            obj[genomic_source]['fastq_1'] = artifact

        elif "wes_reverse" in file_name:
            obj[genomic_source]['fastq_2'] = artifact

    # copy the metadata and add this a new record.
    # note this will clobber whatever is here. This is
    # OK because the original copy of ct will have the
    # clobbered data, while the new copy will have
    # the new entry which will get appended to the
    # "records" list by the merge by ID strategy
    # specified in the json-schema for records
    ct_copy = copy.deepcopy(ct)
    aliquot_obj = _get_source(ct_copy, keypath, level="aliquot")
    aliquot_obj['assay']['wes']['records'][0]['files'] = obj

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
        file_size_bytes: integer specifying the numebr of bytes in the file
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
