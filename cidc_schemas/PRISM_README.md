# Prism-related functions

This document goes over code flows and processes related to prism.

## Load and validate schema

`json_validation.py` defines the `load_and_validate_schema()` function to load and validate schemas from within the data model.
Prism uses this function to load both the template's root object schema as well the preamble's object schema.

1. first loads the schema without and validation with `_load_dont_validate_schema()`

    1. strips off any pointers to within the schema file

    2. loads the JSON definition of the schema

    3. follows any pointers within the file that were removed before

    4. maps or resolves (default) references. for resolving:

        1. does NOT resolve references within the same document. resolving local references here would break recursive schemas

        2. uses `jsonschema.RefResolver` to resolve all other references relative to the schema root directory

2. then uses modifed `jsonschema.Draft7Validator` to validate the schema is valid. the modification allows for internal data validation between different branches of the metadata tree using `in_doc_ref_pattern`.

3. it then either returns the validated schema itself, or a modified validator to apply the schema.

## Loading a template

`template.py` defines the `Template` class to load and process the values from an excel.
Prism is passed the relevant `Template` for the excel template that it's `prismify`ing.

This process begins when the `Template` is first loaded via `Template.from_type` or `Template.from_json`.
The former looks up the template path and calls the latter. That:

1. loads the template schema with `_load_dont_validate_schema`, see "Load and validate schema > 1" above

2. loops through each worksheet to load their field name-schema mappings

    1. validates that the different sections are able to handled, eg preamble, data, arbitary data

    2. loops through each section, making a mapping from the field names (in lowercase) and their schemas. for the data section goes through each subsection

3. loops through each worksheet to generate a key lookup as a mapping from the field name to a list of their field definitions

    1. loops through the preamble rows, processing each schema entry into a list of field definitions

        1. unless `do_not_merge` is set, loads the correct type coercion and marks down all of the other defintion fields

    2. loops through each subsection of the data columns, processing each of their entries the same way

    3. does NOT go through the arbitrary data section, which is currently unused

## Processing a field value

`template.py`'s `Template` class defines the `process_field_value()` function to load and process the values from a single excel field into a metadata change and a list of new files.
Prism calls this function on the `Template` for every value that it finds using the template schema definitions, using the combined preamble and data row as the context for evaluating wildcard values.

1. get the worksheet mappings to both the field definitions and individual field schemas

2. it tries to find the field definitions to parse the field. if it's only found in the arbitrary data section of the schema, it returns an `AtomicChange` mapping the sanitized field name to the raw value.

3. uses the field definition to parse the set of changes and associated local files

    1. if empty and `allow_empty` is set, then does nothing. also does nothing if `do_not_merge` is set.

    2. if `parse_through` is defined, recasts the raw value through this function using the passed context.

    3. if `encrypt` is set, runs the values through the passed encryption function (generally `cidc_schemas.prism.core._encrypt`, based on a SHA512 hash)

    4. if `is_artifact` is `multi`, splits the provided comma-separate value and formats each artifact individually. otherwise if `is_artifact` is set, formats that single artifact.

        1. if the given GCS URI format is a JSON object definition with a function to check errors, evaluate it to see if it generates an error

        2. format the GCS URI key based on the given format in the passed context

        3. validate that the passed value has the correct file extension based on the target GCS URI key

        4. calculate the facet group from the GCS URI format, removing all wildcards and clearing any doubled slashes

        5. make an entry noting to ask the CLI for the file, using a random uuid as an upload placeholder

        6. add the upload placeholder and facet group to the correct spot of the change to return

    5. if `is_artifact` is not set, add the the processed value to the change to return directly

4. return the metadata change and accumulated list of new files
