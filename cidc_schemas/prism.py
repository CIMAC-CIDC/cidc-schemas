# -*- coding: utf-8 -*-

"""Main module."""
import yaml
import jsonschema
import urllib
from openpyxl import load_workbook

SCHEMA_ROOT = "https://raw.githubusercontent.com/CIMAC-CIDC/schemas/testing/schemas"
SCHAMAS = [ \
  "aliquot.yaml", \
  "artifact.yaml", \
  "clinical_trial.yaml", \
  "participant.yaml", \
  "sample.yaml", \
  "shipping_core.yaml", \
]

def split_manifest(file_path, mapping, coercion):
  """ splits manifest into different objects"""

  # load the workbook
  wb = load_workbook(file_path)
  names = wb.sheetnames

  # make sure there are not extra things.
  assert len(names) == 1

  # get sheet
  sheet = wb[names[0]]

  # loop over rows
  doc_header_tups = []
  data_row_tups = []
  headers = []
  seen_tobefilled = False
  seen_plusone = False
  for row in sheet.iter_rows():
    
    # skip explanatory line after seen_tobefileld.
    if seen_tobefilled and not seen_plusone:
      seen_plusone = True
      continue

    # get data.
    line = []
    for col in row:
      line.append(col)

    # check if we have seen data header row
    values = []
    if len(headers) > 0:
      
      # get all values
      for c in line:
        values.append(c.value)

      # zip the header, values.
      for h, v in zip(headers, values):
        data_row_tups.append((h, v))

      # skip rest of logic
      continue

    # check if its a header: key, value row
    if line[0].value is not None and line[1].value is not None and line[2].value is None:
      key = line[0].value
      key = key.replace(":", "")    # these keys have :, strip that out
      value = line[1].value
      doc_header_tups.append((key, value))


    # check if we are in data section
    if line[0].value == "To be filled by Biorepository":
      seen_tobefilled = True

    # check first if valid
    if seen_tobefilled and seen_plusone:

      # check if we are header row
      is_valid = False
      if line[0].value is not None:
        is_valid = line[0].value.lower() in mapping

      # grab headers
      if is_valid:
        for c in line:
          headers.append(c.value)

  # coerce common data types and make lower-case
  tmp = []
  for k, v in doc_header_tups:

    # sanity check
    assert k is not None,  "Malformed header section in spreadsheet"

    k = k.lower()
    v = coerce_value(coercion, k, v)
    tmp.append((k, v))
  doc_header_tups = tmp

  tmp = []
  for k, v in data_row_tups:

    # sanity check
    assert k is not None, "Malformed data rows in spreadsheet"
      
    k = k.lower()
    v = coerce_value(coercion, k, v)
    tmp.append((k, v))
  data_row_tups = tmp

  # return doc and data
  return doc_header_tups, data_row_tups

def coerce_value(coercion, k, v):
  """ coerces values to type """

  # check if we have a coercer.
  if k in coercion:
    try:
      v = coercion[k](v)
    except ValueError as e:
      pass # emit no error, this will fail at normal validation phase
  return v

def validate_schema(schema, instance):
  """ does json-schema validaiton """

  return jsonschema.validate(instance=instance, schema=schema)

def load_schemas():

  # loop over schemas
  schemas = {}
  mapping = {}
  coercion = {}
  for x in SCHAMAS:

    # load the schemas.
    schema_url = "%s/%s" % (SCHEMA_ROOT, x)
    x = urllib.request.urlopen(schema_url)
    txt = x.read()
    schema = yaml.load(txt, Loader=yaml.FullLoader)

    # save teh id.
    schema_id = schema['id']
    schemas[schema_id] = schema

    # get the properties.
    for key in schema['properties'].keys():
      
      # can't already exist
      assert key not in mapping

      # add our own type conversion
      t = schema['properties'][key]['type']
      if t == 'string':
        coercion[key] = str
      elif t == 'integer':
        coercion[key] = int
      elif t == 'number':
        coercion[key] = float

      # store a lookup.
      mapping[key] = schema_id

  return schemas, mapping, coercion

def validate_instance(path_to_manifest):
  """ validates a given schema"""

  # load schemas
  schemas, mapping, coercion = load_schemas()

  # split it out into simple tuples.
  doc_header_tups, data_row_tups = split_manifest(path_to_manifest, mapping, coercion)

  # make the header objects (this is a one object per file)
  head_objs = {}
  data_objs = {}

  # look for the appropriate object.
  for k, v in doc_header_tups:

    # test sanity
    assert k in mapping, "un-recognized property in header"
    schema = mapping[k]

    # bootstrap
    if schema not in head_objs:
      head_objs[schema] = {}

    # save
    head_objs[schema][k] = v

  # validate the header objects.
  for schema_id in head_objs:

    # validate this.
    try:
      validate_schema(schemas[schema_id], head_objs[schema_id])
    except jsonschema.exceptions.ValidationError as e:
      raise e
      print("validation error")
      print(e.validator)
      print(e.validator_value)
      print(e.schema)
      print(e.schema_path)
      print(e.message)


  # look for the appropriate object.
  for k, v in data_row_tups:

    # test sanity
    assert k in mapping, "un-recognized property in data"
    schema = mapping[k]

    # bootstrap
    if schema not in data_objs:
      data_objs[schema] = {}

    # save
    data_objs[schema][k] = v

  # validate the header objects.
  for schema_id in data_objs:

    # validate this.
    print(data_objs[schema_id])
    try:
      validate_schema(schemas[schema_id], data_objs[schema_id])
    except jsonschema.exceptions.ValidationError as e:
      raise e
      print("validation error")
      print(e.validator)
      print(e.validator_value)
      print(e.schema)
      print(e.schema_path)
      print(e.message)

  return head_objs, data_objs