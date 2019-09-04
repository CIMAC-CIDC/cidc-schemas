import os

from cidc_schemas.util import parse_npx

from .constants import TEST_DATA_DIR


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
    
