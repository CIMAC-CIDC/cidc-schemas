import json
import os
import pytest
import jsonschema
from deepdiff import DeepSearch, grep
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
        "ref": ref
      }

    # BIG OLD TODO HERE TO FIGURE THIS OUT.
    #dat_cols = t2[ws]['data_columns']
    #print(dat_cols.keys())

  return key_lu

def _find_it(key: str, schema: dict, key_lu: dict):

  # first translate key name.
  key = key.lower()
  schema_key = key_lu[key]["schema_key"]

  # find it in the schema
  ds = schema | grep(schema_key)

  # get the first occurance of it
  return sorted(ds['matched_paths'], key=len)[0]
  
def _set_val(path: str, val: str, trial: dict):
  """ sets the value given the path """

  # first we trim the root entry.
  stop = path.find("]") + 1
  path = path[stop::]

  # then we tokenize the paths.
  paths = path.split("']['")
  paths[0] = paths[0].replace("['", "")
  paths[-1] = paths[-1].replace("']", "")

  print("-", paths)

  # modifier keys
  mods = set([
    "items",
    "properties"
  ])

  # then we loop until we are done.
  curp = trial
  lenp = len(paths)
  for i in range(len(paths)):

    # simplify
    key = paths[i]
    print("--", key)

    # check if its final
    if i == lenp - 1:
      curp[key] = val
      return

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
        else:
          raise NotImplementedError

    # not a modifer so add another level
    else:

      # is there already a key?
      if not key in curp:
        
        # look forward to see what we might add.
        key2 = paths[i+1]

        # its a list.
        if key2 == "items":
          curp[key] = []
          
        else:
          raise NotImplementedError

      # set pointer for next round
      curp = curp[key]




def prismify(xlsx_path: str, template_path: str):
  """
  convert excel file to json object
  """

  # get the schema
  validator, schema = _load_tools()
  key_lu = _load_template(template_path)

  # read the excel file
  t = XlTemplateReader.from_excel(xlsx_path)

  # create the root dictionary.
  root = {}

  # loop over spreadsheet
  worksheet_names = t.grouped_rows.keys()
  for name in worksheet_names:

    # get the worksheat.
    ws = t.grouped_rows[name]

    # Compare preamble rows
    cnt = 0
    for row in ws[RowType.PREAMBLE]:
      key = row[0]
      val = row[1]

      print("-----")
      print()
      print(key, val)
      path = _find_it(key, schema, key_lu)
      print()
      print(path)
      _set_val(path, val, root)
      print()
      print()
      print(root)

      # find this lookup in out dictionary.
      #print("--fin0--")

      cnt += 1
      if cnt > 100:
        break
      

    # Compare data headers
    #gen_headers = gen_ws[RowType.HEADER][0]
    #ref_headers = ref_ws[RowType.HEADER][0]
    # for (gen_h, ref_h) in zip(gen_headers, ref_headers):
    #    assert gen_h == ref_h, error(
    #        f'data: generated template had header {gen_h} where reference had {ref_h}')
    


    print("")
    print("")
    print("blah")

  