# cidc-schemas
| Branch                                                            | Status                                                                                                                             |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| [master](https://cimac-cidc.github.io/cidc-schemas/)              | [![Build Status](https://travis-ci.org/CIMAC-CIDC/cidc-schemas.svg?branch=master)](https://travis-ci.org/CIMAC-CIDC/cidc-schemas)  |

This repository contains formal definitions of the CIDC metadata model using [json-schema](https://json-schema.org/) syntax and vocabulary.

### View documentation at https://cimac-cidc.github.io/cidc-schemas/

## Installation

To install the latest stable version from the `release` branch, run:
```bash
pip install git+https://github.com/cimac-cidc/cidc-schemas@release
```

To install the latest development version from the `master` branch, run:
```bash
pip install git+https://github.com/cimac-cidc/cidc-schemas
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

### Setting up git hooks

This repository contains git hooks in the `.githooks` folder. After cloning it
it's recommended to configure those hooks with

```bash
git config core.hooksPath .githooks
```

### Running tests

This repository has unit tests in the _tests_ folder. After installing dependencies
the tests can be run via the command

```bash
py.test --cache-clear tests
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

### Convert between yaml and json

The CLI comes with a little utility for converting between yaml and json files.

```bash
cidc_schemas convert --to_json <some_yaml_file>
```

## Creating New Excel Templates

### Workflow

A new manifest or assay template has been "added" to the repository once these three things are true:

- A file `schemas/templates/<TEMPLATE TYPE>/<TEMPLATE NAME>.json` exists specifying the template schema.
- A file `template_examples/<TEMPLATE NAME>.xlsx` exists containing a populated example Excel template corresponding to the template schema.
- Running `pytest tests/test_templates.py` generates no errors related to this template.

Here's the recommended workflow for achieving those three things:

1. Create a new git branch and switch to it (naming your branch something like `template-dev-<TEMPLATE NAME>`):
   ```bash
    git checkout -b <YOUR BRANCH NAME>
   ```
2. On this branch, create a new template schema called `<TEMPLATE NAME>.json` in the `schemas/templates/<template-type>` directory. See the template schema structure section below for guidance.
3. Use the CLI to generate an empty Excel template from your schema, and visually verify that the generated template accords with your expectations. Iteratively edit the schema and regenerate the Excel template until you are satisfied.
4. Fill out the generated Excel template with some valid sample values, and place that file in `template_examples` with the name `<TEMPLATE NAME>.xlsx`.
   - **Note**: by this point, you should have created two files:
     1. `schemas/templates/<TEMPLATE TYPE>/<TEMPLATE NAME>.json`
     2. `template_examples/<TEMPLATE NAME>.xlsx`
5. Ensure that `pytest tests/test_templates.py` raises no errors related to this template.
6. Commit and push your changes.
   ```bash
    # Add the two files you've created
    git add schemas/templates/<TEMPLATE TYPE>/<TEMPLATE NAME>.json template_examples/<TEMPLATE NAME>.xlsx
    git commit -m "Added template for <TEMPLATE NAME>"
    git push -u origin <YOUR BRANCH NAME>
   ```
7. Navigate to GitHub and create a pull request. Get feedback on your template.
8. Once your pull request is approved, merge your changes into master. All done!

### Template Schema Structure

The current template generator can create empty Excel workbooks with arbitrarily many worksheets in them from JSON schemas. Every worksheet in the template has the same high level structure made up of two sections:

1. **`preamble_rows`**: a set of key-value rows appearing at the top of the worksheet. This is a good place to have template users input data that applies to, e.g., the entire batch of samples.
2. **`data_columns`**: a data table that appears below `preamble_rows` in each worksheet, containing data headers with columns beneath them with multiple data entries for each header. Data columns are grouped into subtables, where a set of column headers will have one shared header above them (e.g., the shared header "Filled by Biorepository" should appear above all data columns that the biorepository will fill out). This is a good place to have template users input data that will be different for, e.g., each sample.

**Note**: Either of these sections can be omitted from a given worksheet.

The template generator expects JSON schemas with the following structure:

```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": <a unique id for this template>,
  "title": <title appearing at top of every worksheet>,
  "description": <a statement about this template to appear in documentation>
  "properties": {
    "worksheets": {
      <worksheet name>: {
        "preamble_rows": {
          <field name>: <value schema>,
          <field name>: <value schema>,
          ...
        },
        "data_columns": {
          <subtable header>: {
            <field name>: <value schema>,
            <field name>: <value schema>,
            ...
          },
          <subtable header>: {
            ...
          },
          ...
        }
      },
      <worksheet name>: {...}
    }
  }
}
```

Template elements:

- **`<worksheet name>`**: the name for the worksheet as it will appear in Excel.
- **`<field name>`**: a human-readable label for a template field as it should appear in the spreadsheet. In the preamble section, these will be row keys. In the data section, these will be column headers.
- **`<value schema>`**: a reference to a property in another JSON schema in the data model, or a custom JSON schema. The `<value schema>`'s `"type"` and `"format"` properties will be used for cell data validation in the generated Excel spreadsheet.
- **`<subtable header>`**: A shared header that appears in a merged cell above the data column headers specified as properties of this subtable. `<subtable header>`s are only valid as a property of the `"data_columns"` section of the template schema.
