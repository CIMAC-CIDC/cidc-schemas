from .manifest_data import manifest_data_generators
from .assay_data import assay_data_generators
from .analysis_data import analysis_data_generators
from .utils import PrismTestData, get_test_trial


def list_test_data():
    generators = [
        *manifest_data_generators,
        *assay_data_generators,
        *analysis_data_generators,
    ]
    for generator in generators:
        yield generator()
