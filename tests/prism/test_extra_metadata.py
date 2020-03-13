import pytest

from cidc_schemas.prism import extra_metadata

from .test_merger import npx_file_path, npx_combined_file_path, elisa_test_file_path


def test_parse_npx_invalid(npx_file_path):
    # test the parse function by passing a file path
    with pytest.raises(TypeError):
        samples = extra_metadata.parse_npx(npx_file_path)


def test_parse_npx_single(npx_file_path):
    # test the parse function
    f = open(npx_file_path, "rb")
    samples = extra_metadata.parse_npx(f)

    assert samples["number_of_samples"] == 4
    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
    }


def test_parse_npx_merged(npx_combined_file_path):
    # test the parse function
    f = open(npx_combined_file_path, "rb")
    samples = extra_metadata.parse_npx(f)

    assert samples["number_of_samples"] == 9

    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
        "CTTTP05A1.00",
        "CTTTP06A1.00",
        "CTTTP07A1.00",
        "CTTTP08A1.00",
        "CTTTP09A1.00",
    }


def test_parse_elisa_invalid(elisa_test_file_path):
    # test the parse function by passing a file path
    with pytest.raises(TypeError):
        samples = extra_metadata.parse_elisa(elisa_test_file_path)


def test_parse_elisa_single(elisa_test_file_path):
    # test the parse function
    f = open(elisa_test_file_path, "rb")
    samples = extra_metadata.parse_elisa(f)

    assert samples["number_of_samples"] == 7
    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP01A2.00",
        "CTTTP01A3.00",
        "CTTTP02A1.00",
        "CTTTP02A2.00",
        "CTTTP02A3.00",
        "CTTTP02A4.00",
    }
