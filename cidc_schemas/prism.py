import json
import os
import pytest
import copy
import jsonschema
from deepdiff import DeepSearch, grep
from jsonmerge import merge, Merger
from pprint import pprint

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from cidc_schemas.constants import SCHEMA_DIR


def _load_tools():

  # get the schema
  schema_root = SCHEMA_DIR
  schema_path = os.path.join(SCHEMA_DIR, "clinical_trial.json")
  schema = load_and_validate_schema(schema_path, schema_root)

  # create validator assert schemas are valid.
  validator = jsonschema.Draft7Validator(schema)

  # return the validator and schema
  return validator, validator.schema

def _get_coerce(ref: str):

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
    raise NotImplementedError


def _load_template(template_path: str):

  # get the template.
  with open(template_path) as fin:
    t = json.load(fin)

  # create a key lookup dictionary
  key_lu = {}

  # loop over each worksheet
  t2 = t['properties']['worksheets']
  for ws in t2:

    # loop over each row in pre-amble
    pre_rows = t2[ws]['preamble_rows']
    for xlsx_key in pre_rows.keys():

      # get the reference
      ref = pre_rows[xlsx_key]['$ref']
      schema_key = ref.split("/")[-1]

      key_lu[xlsx_key] = {
        "schema_key": schema_key,
        "ref": ref,
        "coerce": _get_coerce(ref)
      }

    # load the data columns
    dat_cols = t2[ws]['data_columns']
    for key1 in dat_cols.keys():
      for key2 in dat_cols[key1]:
        
        # get the reference
        ref = dat_cols[key1][key2]['$ref']
        schema_key = ref.split("/")[-1]

        key_lu[key2] = {
          "schema_key": schema_key,
          "ref": ref,
          "coerce": _get_coerce(ref)
        }

  return key_lu

def _find_it(key: str, schema: dict, key_lu: dict, assay_hint: str = ""):

  # first translate key name.
  key = key.lower()
  schema_key = key_lu[key]["schema_key"]

  # special case1: file_path
  if schema_key == "file_path":
    return "file_path:TODO"

  # find it in the schema
  ds = schema | grep(schema_key)

  # sort
  choices = sorted(ds['matched_paths'], key=len)

  # check if there are more equal length
  choice = choices[0]
  if len(choices) > 1 and len(choices[0]) == len(choices[1]):
    if assay_hint != "":
      for i in range(len(choices)):
        if choices[i].count(assay_hint) > 0:
          choice = choices[i]
          break

  # return chosen one.
  return choice
  
def _set_val(path: str, val: str, trial: dict, verbose=False):
  """ sets the value given the path """

  # first we trim the root entry.
  stop = path.find("]") + 1
  path = path[stop::]

  # then we tokenize the paths.
  tmps = path.split("][")
  for i in range(len(tmps)):
    tmps[i] = tmps[i].replace("'","")
    tmps[i] = tmps[i].replace("[", "")
    tmps[i] = tmps[i].replace("]", "")
  paths = tmps

  if verbose: print("-", paths)

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

    if verbose: print("--", key)

    # short circuit
    if skip_next:
      skip_next = False
      if verbose: print("-skip-", key)
      continue

    # check if its final
    if i == lenp - 1:
      curp[key] = val

      if verbose:
        print("final", json.dumps(trial))
      return

    # check if this is a skiper
    elif key in skipers:
      if verbose: print("-skipers-", key)
      skip_next = True
      continue

    # always skip integers as keys.
    elif isinstance(key, int):
      if verbose: print("-skipers: int-", key)
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
      if not key in curp:
        
        # look forward to see what we might add.
        key2 = paths[i+1]

        if verbose: print("--2", key2)

        # its a list.
        if key2 == "items":
          curp[key] = []
          
        elif key2 == 'properties':
          curp[key] = {}

        elif key2 == 'allOf':
          curp[key] = {}    # this assume allOf always creates object, maybe not true?

        else:
          raise NotImplementedError

      # set pointer for next round
      curp = curp[key]



def prismify(xlsx_path: str, template_path: str, assay_hint: str=""):
  """
  convert excel file to json object
  """

  # get the schema
  validator, schema = _load_tools()
  key_lu = _load_template(template_path)

  # verbosity
  verb = False

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
      
      # simplify
      key = row[0]
      val = row[1]

      # coerce value
      val = key_lu[key.lower()]['coerce'](val)

      # add to dictionary
      path = _find_it(key, schema, key_lu, assay_hint=assay_hint)
      _set_val(path, val, root, verbose=verb)      

    # move to headers
    headers = ws[RowType.HEADER][0]
    
    # get the data.
    data = ws[RowType.DATA]
    for row in data:

      # create dictionary per row
      curd = copy.deepcopy(root)
      for key, val in zip(headers, row):

        # coerce value
        val = key_lu[key.lower()]['coerce'](val)

        # add to dictionary
        path = _find_it(key, schema, key_lu, assay_hint=assay_hint)
        _set_val(path, val, curd, verbose=verb)

      # save the entry
      data_rows.append(curd)

  # prepend header to data rows
  objs = data_rows

  # create the merger
  merger = Merger(schema)

  # iteratively merge.
  cur_obj = objs[0]
  for i in range(1, len(objs)):
    cur_obj = merger.merge(cur_obj, objs[i])

  # return the object.
  return cur_obj
  