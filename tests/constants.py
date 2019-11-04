import os

from cidc_schemas.constants import SCHEMA_DIR

TESTS_DIR = os.path.abspath(os.path.dirname(os.path.join(__file__)))
ROOT_DIR = os.path.join(TESTS_DIR, "..")
TEST_DATA_DIR = os.path.join(TESTS_DIR, "data")
TEST_SCHEMA_DIR = os.path.join(TEST_DATA_DIR, "schemas")
TEMPLATE_EXAMPLES_DIR = os.path.join(ROOT_DIR, "template_examples")
