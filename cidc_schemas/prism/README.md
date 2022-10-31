# Prism

This document goes over code flows and processes related to prism.

## Constants

`prism/constants.py` defines a number of constants that are used across CIDC.

- `SUPPORTED_ASSAYS`, `SUPPORTED_ANALYSES`
  - the list of assays and analyses that the CIDC supports
  - assay data comes in from the CIMACs, analysis data is generated by CIDC
- `SUPPORTED_SHIPPING_MANIFESTS`
  - shipping manifests that CIDC supports from NCI/CSMS
- `SUPPORTED_WEIRD_MANIFESTS`
  - any other metadata-only uploads that CIDC supports
  - currently this is only the WES tumor-normal pairing manifest
- `SUPPORTED_MANIFESTS`
  - all uploads that CIDC supports which do NOT include files
  - the previous two combined
- `SUPPORTED_TEMPLATES`
  - all uploads that CIDC supports
  - all of the previous ones combined
- `ASSAY_TO_FILEPATH`
  - a mapping providing the file prefixes for each assay
  - only used by the API to issue permissions to all GCS files

## Core - Prismify

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

## Extra Metadata parsers

`prism/extra_metadata.py` defines functions for parsing indiviudal files for additional metadata, collecting and counting IDs from within the file itself.
Currently there are 3 implemented:

- `parse_npx()` for olink NPX files
- `parse_elisa()` for ELISA grand serology files
- `parse_clinical()` for Excel or CSV clinical data files

These are called from `prism/merger.py::merge_artifact_extra_metadata()`, itself called from API's `models/models.py::UploadJobs.merge_extra_metadata()` which is triggered by a call to API's `resources/upload_jobs.py::extra_assay_metadata` during the upload process.

## Mergers

`prism/mergers.py` defines functions for merging data into a trial's metadata blob.
There are three specifically for artifact handling and another for a generic metadata patch.

- `merge_artifact()` handles single a file by adding passed metadata into the full metadata blob  
- `merge_artifacts()` provides the same handling for a list of files at a time
- `merge_artifact_extra_metadata()` handles generation and adding of extra metadata from a file, defined by the parsers in `prism/extra_metadata.py`
- `merge_clinical_trial_metadata()` handles arbitrary metadata patches into a clinical trial, relying on `jsonmerge`

## Pipelines

`prism/pipelines.py` defines functions for generating files AFTER an upload successfully merges.
Notably, it generates analysis configurations for RNA and WES for use by the bioinformatics team.
It also records any new participants encountered in a shipping manifest metadata upload, and creates pairing recommendations for new WES assay files.

Each call is made from `generate_analysis_configs_from_upload_patch()`, which is itself called from API's `shared/emails.py::new_upload_alert()` from API's `models/models.py::UploadJobs.alert_upload_success()` from either `UploadJobs.ingestion_success()` (originally called by CFn's `uploads.py::ingest_upload()`) or `UploadJobs.create()` (originally triggered by a request to API's `resources/upload_jobs.py::upload_manifest()`).