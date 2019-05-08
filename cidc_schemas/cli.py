import os
import argparse
from .manifest import ShippingManifest


def main():
    args = interface()
    args.func(args)


def interface() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Parser for template generation
    generate_parser = subparsers.add_parser(
        'generate_template', help='Create shipping manifest excel template from manifest configuration file')
    generate_parser.add_argument('-m', '--manifest_file',
                                 help='Path to yaml file containing template configuration', required=True)
    generate_parser.add_argument('-s', '--schemas_dir',
                                 help='Path to directory containing data entity schemas', required=True)
    generate_parser.add_argument(
        '-o', '--out_file', help='Where to write the resulting excel template', required=True)
    generate_parser.set_defaults(func=generate_template)

    # TODO: complete CLI for validating an excel template
    validate_parser = subparsers.add_parser(
        'validate_template', help='Validate a populated excel template based on the given configuration files')
    validate_parser.set_defaults(func=validate_template)

    return parser.parse_args()


def generate_template(args: argparse.Namespace):
    schemas_dir = os.path.abspath(args.schemas_dir)
    schema_paths = [os.path.join(schemas_dir, path)
                    for path in os.listdir(schemas_dir)]
    ShippingManifest(args.manifest_file, schema_paths).to_excel(args.out_file)


def validate_template(args: argparse.Namespace):
    # TODO: call validation module
    pass


if __name__ == '__main__':
    main()
