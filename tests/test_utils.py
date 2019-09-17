import os
import pytest

from cidc_schemas.util import parse_npx
import cidc_schemas.util as util

from .constants import TEST_DATA_DIR

def test_path_to_typed_tokens():

    assert ['p', 0, 'a', 0, 'id'] == list(util._path_to_typed_tokens("root['p'][0]['a'][0]['id']"))
    assert ['p', 0, 1, 2, 'id'] == list(util._path_to_typed_tokens("root['p'][0][1][2]['id']"))


def test_get_all_paths():
    hier = {
        "p": [{
            "a": [{
                "id": 1,
                "i want": "this"
            },
            {
                "id": 2,
                "and": "this"
            }],
            "id" : "3",
            "and" : "this"
        }]
    }

    assert ["root['p'][0]['a'][0]['id']"] == list(util._get_all_paths(hier, 1))
    assert ["root['p'][0]['a'][1]['id']"] == list(util._get_all_paths(hier, 2))
    assert ["root['p'][0]['id']"] == list(util._get_all_paths(hier, "3"))
    with pytest.raises(KeyError):
        assert (util._get_all_paths(hier, 3))
    
    assert ["root[0]['id']"] == list(util._get_all_paths(hier['p'], "3"))

    assert [
        "root['p'][0]['a'][0]['i want']",
        "root['p'][0]['a'][1]['and']",
        "root['p'][0]['and']"
        ] == sorted(list(util._get_all_paths(hier, "this")))


def test_get_source():

    hier = {
        "p": [{
            "a": [{
                "id": 1
            },
            {
                "id": 2
            }],
            "id" : "3"
        }]
    }

    assert 1 == util._get_source(hier, "root['p'][0]['a'][0]['id']")
    assert 2 == util._get_source(hier, "root['p'][0]['a'][1]['id']")
    assert '3' == util._get_source(hier, "root['p'][0]['id']")
    
    assert util._get_source(hier, "root['p'][0]['a'][1]['id']", skip_last=3) == util._get_source(hier, "root['p'][0]")



def test_parse_npx_invalid():

    # test the parse function
    npx_path = os.path.join(TEST_DATA_DIR, 'olink', 'pizza_assay_1_NPX.xlsx')
    with pytest.raises(FileNotFoundError):
        ids = parse_npx(npx_path)

    # test parsing bad xlsx file.
    bad_path = os.path.join(TEST_DATA_DIR, 'date_examples.xlsx')
    ids = parse_npx(bad_path)

    assert len(ids) == 0


def test_parse_npx_single():

    # test the parse function
    npx_path = os.path.join(TEST_DATA_DIR, 'olink', 'olink_assay_1_NPX.xlsx')
    ids = parse_npx(npx_path)

    assert len(ids) == 4
    assert set(ids) == {'HD_59', 'HD_63', 'HD_32', 'HD_50'}
    

def test_parse_npx_merged():

    # test the parse function
    npx_path = os.path.join(TEST_DATA_DIR, 'olink', 'olink_assay_combined.xlsx')
    ids = parse_npx(npx_path)

    assert len(ids) == 9
    assert set(ids) == {'HD_59', 'HD_63', 'HD_32', 'HD_50',
                        'HD_71', 'HD_72', 'HD_73', 'HD_80',
                        'HD_85'}
    
