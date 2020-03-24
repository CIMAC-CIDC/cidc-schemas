import pytest
from copy import deepcopy
from deepdiff import DeepDiff, grep

from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.prism import (
    prismify,
    merge_clinical_trial_metadata,
    merge_artifact,
    merge_artifact_extra_metadata,
)

from .cidc_test_data import list_test_data, PrismTestData


@pytest.fixture(params=list_test_data())
def prism_test(request):
    return request.param


def assert_metadata_matches(received: dict, expected: dict, upload_entries: list):
    # Take the difference of the received patch and the expected patch.
    # We expect these patchs to differ by upload placeholder UUID only,
    # so the number of differences should equal the number of expected
    # upload entries.
    diff = DeepDiff(received, expected)
    if "values_changed" in diff:
        assert len(diff["values_changed"]) == len(upload_entries)
        for key in diff["values_changed"].keys():
            assert key.endswith("['upload_placeholder']")
    else:
        # For manifest uploads, we expect no artifacts, so there should
        # be no difference between expected and received trial objects.
        assert diff == {}


def test_prismify(prism_test: PrismTestData):
    # Run prismify on the given test case
    patch, upload_entries, errs = prismify(*prism_test.prismify_args)

    # Ensure no errors resulted from the prismify run
    assert len(errs) == 0

    # Compare the received upload entries with the expected upload entries.
    # These should differ by upload placeholder UUID only.
    for received, expected in zip(upload_entries, prism_test.upload_entries):
        assert received.local_path == expected.local_path
        assert received.gs_key == expected.gs_key
        assert received.metadata_availability == expected.metadata_availability

    # Compare the received and expected prism metadata patches
    assert_metadata_matches(patch, prism_test.prismify_patch, upload_entries)


def test_merge_patch_into_trial(prism_test: PrismTestData):
    # Merge the prismify patch into the base trial metadata
    result, errs = merge_clinical_trial_metadata(
        prism_test.prismify_patch, prism_test.base_trial
    )

    # Ensure no errors resulted from the merge
    assert len(errs) == 0

    # Ensure that the merge result passes validation
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(result)

    assert_metadata_matches(result, prism_test.target_trial, prism_test.upload_entries)


def test_merge_artifacts(prism_test: PrismTestData):
    # Some upload types won't have any artifacts to merge
    if len(prism_test.upload_entries) == 0:
        return

    # Merge the upload entries into the prismify patch
    uuids_and_artifacts = []
    patch = deepcopy(prism_test.prismify_patch)
    for entry in prism_test.upload_entries:
        patch, artifact, additional_metadata = merge_artifact(
            patch,
            artifact_uuid=entry.upload_placeholder,
            object_url=entry.gs_key,
            assay_type=prism_test.upload_type,
            file_size_bytes=0,
            uploaded_timestamp="",
            md5_hash="foo",
            crc32c_hash="bar",
        )

        # TODO: Check that the artifact contains expected attributes
        # TODO: Check additional_metadata has expected structure

        # Keep track of the artifact metadata
        uuids_and_artifacts.append((entry.upload_placeholder, artifact))

    # Check that the artifact objects have been merged in the right places.
    # First, make an alias `root` for `patch`, because `deepdiff.grep` generates dictionary
    # paths like "root['key1']['key2']['upload_placeholder']".
    root = patch
    placeholder_key = "['upload_placeholder']"
    for uuid, artifact in uuids_and_artifacts:
        # Get the path in the *original* patch to the placeholder uuid.
        paths = (prism_test.prismify_patch | grep(uuid))["matched_values"]
        assert len(paths) == 1, "UUID should only occur once in a metadata patch"
        path = paths.pop()
        assert path.endswith(
            placeholder_key
        ), f"UUID values should have key {placeholder_key}"
        path = path[: -len(placeholder_key)]

        # Ensure that evaluating this same path in the *new* patch gets the expected
        # artifact metadata dictionary.
        assert eval(path) == artifact

    # Merge the patch-with-artifacts into the base trial
    result, errs = merge_clinical_trial_metadata(patch, prism_test.base_trial)

    # Make sure the modified patch is still valid
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(result)
