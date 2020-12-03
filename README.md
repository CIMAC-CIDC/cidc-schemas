# cidc-schemas

| Branch                                               | Status                                                                                                                           | Maintainability                                                                                                                                                          | Test Coverage                                                                                                                                                      | Code Style                                                                                                                                |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [master](https://cimac-cidc.github.io/cidc-schemas/) | ![Continuous Integration](https://github.com/CIMAC-CIDC/cidc-schemas/workflows/Continuous%20Integration/badge.svg?branch=master) | [![Maintainability](https://api.codeclimate.com/v1/badges/3f989b974663df81ef45/maintainability)](https://codeclimate.com/github/CIMAC-CIDC/cidc-schemas/maintainability) | [![Test Coverage](https://api.codeclimate.com/v1/badges/3f989b974663df81ef45/test_coverage)](https://codeclimate.com/github/CIMAC-CIDC/cidc-schemas/test_coverage) | <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a> |

This repository contains formal definitions of the CIDC metadata model using [json-schema](https://json-schema.org/) syntax and vocabulary.

### View documentation at https://cimac-cidc.github.io/cidc-schemas/

## Installation

To install the latest released version, run:

```bash
pip install cidc-schemas
```

## Development

### Project Structure

- **`cidc_schemas/`** - a python module for generating, validating, and reading manifest and assay templates.
  - **`schemas/`** - json specifications defining the CIDC metadata model.
    - `templates/` - schemas for generating and validating manifest and assay templates.
    - `assays/` - schemas for defining assay data models.
    - `artifacts/` - schemas for defining artifacts.
- **`docs/`** - the most recent build of the data model documentation, along with templates and scripts for re-generating the documentation.
- **`template_examples/`** - example populated Excel files for template specifications in `schemas/templates`, and `.csv`s auto-generated from those `.xlsx`s that allow to transparently keep track of changes in them.
- **`tests/`** - tests for the `cidc_schemas` module.
- **`.githooks/`** - git hooks, e.g. for auto-generate `.csv`s in `template_examples/`.

### Developer Setup

Install necessary dependencies.

```bash
pip install -r requirements.dev.txt
```

Install and configure pre-commit hooks.

```bash
pre-commit install
```

### Running tests

This repository has unit tests in the _tests_ folder. After installing dependencies
the tests can be run via the command

```bash
pytest tests
```

### Building documentation

To build the documentation, run the following commands:

```bash
python setup.py install # install helpers from the cidc_schemas library
python docs/generate_docs.py
```

This will output the generated html documents in `docs/docs`. If the updated docs are pushed up and merged
into master, they will be viewable at https://cimac-cidc.github.io/cidc-schemas/.

## Using the Command-Line Interface

This project comes with a command-line interface for validating schemas and generating/validating assay and manifest templates.

### Install the CLI

Clone the repository and cd into it

```bash
git clone git@github.com:CIMAC-CIDC/cidc-schemas.git
cd cidc-schemas
```

Install the `cidc_schemas` package (this adds the `cidc_schemas` CLI to your console)

```bash
python setup.py install
```

Run `cidc_schemas --help` to see available options.

If you're making changes to the module and want those changes to be reflected in the CLI without reinstalling the `cidc_schemas` module every time, run

```bash
python3 -m cidc_schemas.cli [args]
```

### Generate templates

Create a template for a given template configuration.

```bash
cidc_schemas generate_template -m templates/manifests/pbmc_template.json -o pbmc.xlsx
```

### Validate filled-out templates

Check that a populated template file is valid with respect to a template specification.

```bash
cidc_schemas validate_template -m templates/manifests/pbmc_template.json -x template_examples/pbmc_template.xlsx
```

### Validate JSON schemas

Check that a JSON schema conforms to the JSON Schema specifications.

```bash
cidc_schemas validate_schema -f shipping_core.json
```
