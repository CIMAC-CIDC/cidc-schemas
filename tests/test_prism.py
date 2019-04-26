#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_prism` package."""

import os
import unittest
import pytest
import jsonschema

from cidc_schemas import prism

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

class Test_prism(unittest.TestCase):
    """Tests for `cidc_prism` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

        # load schemas
        schemas, mapping, coercion = prism.load_schemas()

        # split it out into simple tuples.
        doc_header_tups, data_row_tups = prism.split_manifest(os.path.join(CUR_DIR, 'data/pbmc_shipping.xlsx'), mapping, coercion)

        # make the header objects (this is a one object per file)
        head_objs = {}
        data_objs = {}
        
        # look for the appropriate object.
        for k, v in doc_header_tups:

          # test sanity
          assert k in mapping
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
            prism.validate_schema(schemas[schema_id], head_objs[schema_id])
          except jsonschema.exceptions.ValidationError as e:
            print("validation error")
            print(e.validator)
            print(e.validator_value)
            print(e.schema)
            print(e.schema_path)
            print(e.message)
  

        # look for the appropriate object.
        for k, v in data_row_tups:

          # test sanity
          assert k in mapping
          schema = mapping[k]

          # bootstrap
          if schema not in data_objs:
            data_objs[schema] = {}

          # save
          data_objs[schema][k] = v

        # validate the header objects.
        for schema_id in data_objs:

          # validate this.
          try:
            prism.validate_schema(schemas[schema_id], data_objs[schema_id])
          except jsonschema.exceptions.ValidationError as e:
            print("validation error")
            print(e.validator)
            print(e.validator_value)
            print(e.schema)
            print(e.schema_path)
            print(e.message)
  

      

        #cidc_prism.validation()
        #assert False
