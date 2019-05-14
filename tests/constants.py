import os

ROOT_DIR = os.path.abspath(os.path.join(__file__, '..', '..'))
SCHEMA_DIR = os.path.join(ROOT_DIR, 'schemas')
TEST_DATA_DIR = os.path.join(__file__, 'data')

# TODO: delete these once manifests are expressed as schemas
SCHEMA_PATHS = [os.path.join(SCHEMA_DIR, path)
                for path in os.listdir(SCHEMA_DIR)]
MANIFEST_DIR = os.path.join(ROOT_DIR, 'manifests')
