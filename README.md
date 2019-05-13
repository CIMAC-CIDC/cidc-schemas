# cidc-schemas

This repository contains formal definitions of the CIDC metadata model using [json-schema](https://json-schema.org/) syntax and vocabulary.

### View documentation at https://cimac-cidc.github.io/cidc-schemas/

## Development

### Project Structure

- **`bin/`** - useful scripts for working with the project.
- **`cidc_schemas/`** - a python module for generating, validating, and reading manifest templates.
- **`docs/`** - the most recent build of the schema documentation, served at https://cimac-cidc.github.io/cidc-schemas/.
- **`manifests/`** - manifest template specifications and example Excel files.
- **`schemas/`** - json specifications defining the CIDC metadata model.
- **`templates/`** - HTML templates for generating schema documentation
- **`tests/`** - tests for the `cidc_schemas` module.

### Running tests

This repository has unit tests in the _tests_ folder. After installing dependencies
the tests can be run via the command

```bash
py.test --cache-clear tests
```

### Building documentation

The documentation can be built by running the following command

```bash
python bin/generate_docs.py
```

This will create the html documents in /docs. If the changes are comitted and pushed
to master this they will be viewable at https://cimac-cidc.github.io/cidc-schemas/

## Using the Command-Line Interface

This project comes with a command-line interface for performing common operations related to schema and manifest definitions.

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

Create a template for a given manifest configuration.

```bash
cidc_schemas generate_template -m manifests/pbmc/pbmc.yaml -s schemas -o pbmc.xlsx
```

### Validate filled-out templates

Check that a populated manifest file is valid with respect to a template specification.

```bash
cidc_schemas validate_template -m manifests/pbmc/pbmc.json -x manifests/pbmc/pbmc.xlsx -s schemas
```

### Convert between yaml and json

The CLI comes with a little utility for converting between yaml and json files.

```bash
cidc_schemas convert --to_json <some_yaml_file>
```
