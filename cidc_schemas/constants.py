import os

SCHEMA_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "schemas")
SCHEMA_LIST = [f'{d}/{f}'.replace(f'{SCHEMA_DIR}/', '')
               for d, _, fs in os.walk(SCHEMA_DIR) for f in fs]

TEMPLATE_DIR = os.path.join(SCHEMA_DIR, 'templates')
