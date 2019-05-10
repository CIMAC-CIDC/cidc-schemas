#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_prism` package."""

import os
import unittest
import pytest
import json
import jsonschema

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
SCHEMA_DIR = os.path.abspath(os.path.join(ROOT_DIR, 'schemas'))

class TestSchemas(unittest.TestCase):
    """Tests for schemas package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""


    def load_schema(self, path):
      
      with open(path) as fin:
        schema = json.load(fin)

      return schema

    def validate_schema(self, name, schema_dir=SCHEMA_DIR):
        # load the schema
        schema_path = os.path.join(schema_dir, '%s.json' % name)
        schema = self.load_schema(schema_path)

        # create local resolver
        resolver = jsonschema.RefResolver(
          'file:{}'.format(SCHEMA_DIR),     # note this is always root of schemas
          schema
        )

        # validate this (raises schema error)
        ival = jsonschema.Draft7Validator(schema=schema, resolver=resolver)
        ival.check_schema(schema)

    def test_mif(self):
        """Test artifact"""

        # for now we manually validate the sub-schemas.
        self.validate_schema("antibody", schema_dir=os.path.join(SCHEMA_DIR, "assays", "components"))
        self.validate_schema("image", schema_dir=os.path.join(SCHEMA_DIR, "assays", "components"))

        # finally validate the good ole boy
        self.validate_schema("mif", schema_dir=os.path.join(SCHEMA_DIR, "assays"))
        assert False


    def test_aliquot(self):
        """Test artifact"""
        self.validate_schema("aliquot")

    def test_artifact(self):
        """Test artifact"""
        self.validate_schema("artifact")

    def test_clinical_trial(self):
        """Test clinical trial"""
        self.validate_schema("clinical_trial")

    def test_participant(self):
      """Test participant"""
      self.validate_schema("participant")

    def test_sample(self):
      """Test sample"""
      self.validate_schema("sample")

    def test_shipping_core(self):
      """Test shipping_core"""
      self.validate_schema("shipping_core")

    def test_user(self):
      """Test user"""
      self.validate_schema("user")
      
    def test_wes_artifact(self):
      """Test wes_artifact"""
      self.validate_schema("wes_artifact")
      
