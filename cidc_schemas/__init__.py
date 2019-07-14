# -*- coding: utf-8 -*-

"""Top-level package for cidc_prism."""

__author__ = """James Lindsay"""
__email__ = 'jlindsay@jimmy.harvard.edu'
__version__ = '0.1.0'

from typing import Union, BinaryIO

from .template import Template


def validate_xlsx(xlsx: Union[str, BinaryIO], schema_path: str, raise_validation_errors: bool = True):
    """Check if a populated .xlsx template file is valid w.r.t. the schema at schema_path"""
    template = Template.from_json(schema_path)
    validation = template.validate_excel(xlsx, raise_validation_errors)
    return validation
