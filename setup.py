#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import glob
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    author="James Lindsay",
    author_email='jlindsay@jimmy.harvard.edu',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="The CIDC data model and tools for working with it.",
    python_requires='>=3.6',
    install_requires=requirements,
    license="MIT license",
    # TODO: work this out - we can't mix content types (.md and .rst)
    # in the long_description.
    # long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='cidc_schemas',
    name='cidc_schemas',
    packages=find_packages(include=['cidc_schemas']),
    test_suite='tests',
    url='https://github.com/CIMAC-CIDC/schemas',
    version='0.1.3',
    zip_safe=False,
    entry_points={
        'console_scripts': ['cidc_schemas=cidc_schemas.cli:main']
    }
)
