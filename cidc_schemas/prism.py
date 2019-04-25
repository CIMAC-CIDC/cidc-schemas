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
  for row in sheet.iter_rows():
    
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

    # check if all values filled.
    fail = False
    for i in range(len(line)):
      if line[i].value is None:
        fail = True

    # check first if valid
    if not fail:

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
    k = k.lower()
    v = coerce_value(coercion, k, v)
    tmp.append((k, v))
  doc_header_tups = tmp

  tmp = []
  for k, v in data_row_tups:
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

  # validate stuff
  #jsonschema.validate(instance=instance, schema=schema)
