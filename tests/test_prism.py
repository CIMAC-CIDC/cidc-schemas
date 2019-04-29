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

    def test_pbcm(self):
      """test static pbmc"""

      # test pbmc
      path_to_manifest = os.path.join(CUR_DIR, 'data/pbmc_shipping.xlsx')
      head_objs, data_objs = prism.validate_instance(path_to_manifest)

      assert len(head_objs) > 0
      assert len(data_objs) > 0