import json
import os
import copy
import jsonschema
from deepdiff import grep
from jsonmerge import merge, Merger

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from cidc_schemas.constants import SCHEMA_DIR


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

    # get just the json file
    file_path = ref.split("#")[0]
    prop = ref.split("properties/")[-1]

    # load the schema
    with open(os.path.join(SCHEMA_DIR, file_path)) as fin:
        schema = json.load(fin)

    # get the entry
    entry = schema['properties'][prop]

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

                # also a dictionary, just will be proceeded by a nunber
                elif key2 == 'allOf':
                    # this assume allOf always creates object, maybe not true?
                    curp[key] = {}

                else:
                    raise NotImplementedError

            # set pointer for next round
            curp = curp[key]


def _process_property(
                    row: list, 
                    key_lu: dict,
                    schema: dict,
                    data_obj: dict,
                    assay_hint: str,
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
        # TODO: need to implement code dealing with file validation
        return

    # add to dictionary
    path = _find_key(schema_key, schema, assay_hint=assay_hint)
    _set_val(path, val, data_obj, verbose=verb)


def prismify(xlsx_path: str, template_path: str, assay_hint: str = "", verb: bool = False):
    """
    Converts excel file to json object.

    Args:
        xlsx_path: file on file system to excel file.
        template_path: path on file system relative to schema root of the temaplate
                
        assay_hint: string used to help idnetify properties in template. Must be the
                    the root of the template filename i.e. wes_template.json would 
                    be wes.
        verb: boolean indicating verbosity

    Returns:
        None, data_obj is modified in place

    """

    # get the schema and validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    key_lu = _load_keylookup(template_path)

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
            _process_property(row, key_lu, schema, root, assay_hint, verb)

        # move to headers
        headers = ws[RowType.HEADER][0]

        # get the data.
        data = ws[RowType.DATA]
        for row in data:

            # create dictionary per row
            curd = copy.deepcopy(root)
            for key, val in zip(headers, row):

                # process this property
                _process_property([key, val], key_lu, schema, curd, assay_hint, verb)

            # save the entry
            data_rows.append(curd)

    # create the merger
    merger = Merger(schema)

    # iteratively merge.
    cur_obj = data_rows[0]
    for i in range(1, len(data_rows)):
        cur_obj = merger.merge(cur_obj, data_rows[i])

    # return the object.
    return cur_obj
