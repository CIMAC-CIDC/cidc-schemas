#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import pytest

from cidc_schemas.json_validation import _map_refs


def test_map_refs():
    spec = {
        'a': {
            '$ref': 'foo'
        },
        'b': [
            {'$ref': 'foo'}
        ]
    }

    target = {
        'a': 'FOO',
        'b': ['FOO']
    }

    assert _map_refs(spec, lambda ref: ref.upper()) == target
