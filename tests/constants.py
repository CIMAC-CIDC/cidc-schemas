import os

TESTS_DIR = os.path.abspath(os.path.dirname(os.path.join(__file__)))
ROOT_DIR = os.path.join(TESTS_DIR, '..')
SCHEMA_DIR = os.path.join(ROOT_DIR, 'schemas')
TEST_DATA_DIR = os.path.join(TESTS_DIR, 'data')
TEMPLATE_EXAMPLES_DIR = os.path.join(ROOT_DIR, 'template_examples')
