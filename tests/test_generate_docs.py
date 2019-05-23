#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for doc generation."""

import os
import unittest
import pytest
from docs import generate_docs

from .constants import ROOT_DIR


def count_files(directory):
    return sum([len(files) for _, _, files in os.walk(directory)])


def test_generate_docs():
    """A smoke test that just asserts that we generated the expected number of files"""

    generate_docs.generate_docs()

    # Count all schemas
    num_schemas = count_files(os.path.join(ROOT_DIR, 'schemas'))

    # Count all documentation files
    num_docs = count_files(os.path.join(ROOT_DIR, 'docs', 'docs'))

    # Minus the index file
    assert num_schemas == num_docs - 1
