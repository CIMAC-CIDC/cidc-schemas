#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cidc_prism` package."""

import os
import unittest
import pytest
from docs import generate_docs

from .constants import ROOT_DIR


@pytest.mark.skip("waiting on updates for manifest/assay template schema documentation generation")
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
