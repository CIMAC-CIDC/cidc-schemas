#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_prism` package."""

import os
import unittest
import pytest
import yaml
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
        schema = yaml.load(fin.read(), Loader=yaml.FullLoader)

      return schema

    def validate_schema(self, name):
        # load the schema
        schema_path = os.path.join(SCHEMA_DIR, '%s.yaml' % name)
        schema = self.load_schema(schema_path)

        # validate this (raises schema error)
        ival = jsonschema.Draft7Validator(schema=schema)
        ival.check_schema(schema)

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
      
