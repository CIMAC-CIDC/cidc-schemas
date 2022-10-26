# Prism

This document goes over code flows and processes related to prism.

## Prismify

`prism/core.py` defines the `prismify()` function to validate and translate an excel template into a JSON patch.
The API loads a submitted upload template file as a `cidc_schemas.template_reader.XlTemplateReader` and passes it to `prismify` along with the corresponding loaded `cidc_schemas.template.Template`, which then does the following:

1. validates the template's type is supported by prism

2. loads and validates the template's root object schema using `json_validation`.
This is defined for some templates, but otherwise is the root clinical trial schema itself.

3. sets up the return as an empty clinical trial and gets a reference to the template's root object. also begin a list for files to request from the CLI, as well as a list for errors that are encountered.

4. loops through each worksheet in the schema

    1. makes key-value mapping from the preamble section to use for decoding the data

    2. loads and validates the preamble's object schema

    3. sets up an empty reference to the preamble's object relative to the template's root object

    4. loops through each data row in the upload template

        1. makes key-value mapping from that row, adding in the preamble data too

        2. sets up an empty reference to the data's object relative to the preamble's object

        3. loops through each field in the template's data section schema

            1. uses the combined data and preamble context to process the value into a change and a list of new files

            2. then applies these changes to the data object, and add the new files to the global list to get from the CLI

        4. update the preamble object with our new filld out data object, noting any errors

    5. loops through each field in the template's preamble section schema

        1. uses the preamble context to process the value into a change and a list of new files

        2. then applies these changes to the preamble object, and add the new files to the global list to get from the CLI

    6. update the template's root object with our new filled out preamble object, noting any errors

5. update the return object if needed with our new filled out template root object, noting any errors

6. return the new patch object, the list of files to get from the CLI, and any errors encountered along the way
