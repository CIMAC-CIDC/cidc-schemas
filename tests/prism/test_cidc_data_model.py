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


@pytest.fixture
def ct_validator():
    return load_and_validate_schema("clinical_trial.json", return_validator=True)


def assert_metadata_matches(received: dict, expected: dict, upload_entries: list):
    """Check that the `received` metadata dict matches the `expected` metadata dict."""
    # Take the difference of the received patch and the expected patch.
    # We expect these patchs to differ by upload placeholder UUID only,
    # so the number of differences should equal the number of expected
    # upload entries.
    diff = DeepDiff(expected, received)
    if upload_entries and diff:
        assert len(diff) == 1  # only "values_changed"
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
    received = [
        (e.local_path, e.gs_key, e.metadata_availability) for e in upload_entries
    ]
    expected = [
        (e.local_path, e.gs_key, e.metadata_availability)
        for e in prism_test.upload_entries
    ]

    assert sorted(expected) == sorted(received)
    for received, expected in zip(
        sorted(upload_entries), sorted(prism_test.upload_entries)
    ):
        assert received.local_path == expected.local_path
        assert received.gs_key == expected.gs_key
        assert received.metadata_availability == expected.metadata_availability

    # Compare the received and expected prism metadata patches
    assert_metadata_matches(patch, prism_test.prismify_patch, upload_entries)


def test_merge_patch_into_trial(prism_test: PrismTestData, ct_validator):
    # Merge the prismify patch into the base trial metadata
    result, errs = merge_clinical_trial_metadata(
        prism_test.prismify_patch, prism_test.base_trial
    )

    # Ensure no errors resulted from the merge
    if errs:
        raise errs[0]
    assert len(errs) == 0

    # Ensure that the merge result passes validation
    ct_validator.validate(result)

    assert_metadata_matches(result, prism_test.target_trial, prism_test.upload_entries)


def test_merge_artifacts(prism_test: PrismTestData, ct_validator):
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

        # Check that artifact has expected fields for the given entry
        assert artifact["object_url"] == entry.gs_key
        assert artifact["upload_placeholder"] == entry.upload_placeholder
        assert additional_metadata != {}

        # Keep track of the artifact metadata
        uuids_and_artifacts.append((entry.upload_placeholder, artifact, entry))

    # Check that the artifact objects have been merged in the right places.
    placeholder_key = "['upload_placeholder']"
    for uuid, artifact, entry in uuids_and_artifacts:
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
        assert eval(path, {}, {"root": patch}) == artifact

    # Merge the patch-with-artifacts into the base trial
    result, errs = merge_clinical_trial_metadata(patch, prism_test.base_trial)
    assert len(errs) == 0

    # Make sure the modified patch is still valid
    ct_validator.validate(result)
