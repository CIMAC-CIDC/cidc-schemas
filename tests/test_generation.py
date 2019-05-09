#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_prism` package."""

import os
import unittest
import pytest
from bin import generate_docs


ROOT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
SCHEMA_DIR = os.path.abspath(os.path.join(ROOT_DIR, 'schemas'))


def test_doc_generation():
    # a smoke test that just asserts the number of html files is 1 + # schemas

    # run the function.
    generate_docs.generate_docs()

    # assert the number of htmls are the same.
    num_schema = len(os.listdir(os.path.join(ROOT_DIR, 'schemas')))
    num_manifest = len(os.listdir(os.path.join(ROOT_DIR, 'manifests')))

    files = os.listdir(os.path.join(ROOT_DIR, 'docs'))
    keep = []
    for f in files:
        if f.count("html") > 0:
            keep.append(f)

    assert len(keep) == num_schema + num_manifest
