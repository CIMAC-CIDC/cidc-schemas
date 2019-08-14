#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for doc generation."""

import os
import unittest
import pytest
from docs import generate_docs

from cidc_schemas.constants import SCHEMA_DIR


def count_files(directory):
    return sum([len(files) for _, _, files in os.walk(directory)])


def test_generate_docs(tmpdir):
    """A smoke test that just asserts that we generated the expected number of files"""

    generate_docs.generate_docs(tmpdir)

    # Count all schemas
    num_schemas = count_files(SCHEMA_DIR)

    # Count all documentation files
    num_docs = count_files(tmpdir)

    # .HTMLs and .FULL.JSONs minus the index file
    assert 2*num_schemas == num_docs - 1
