import os
import argparse
from . import util
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

    # Parser for schema file format conversion
    conversion_parser = subparsers.add_parser(
        'convert', help='Convert a yaml file to a json file, or vice versa')
    conversion_parser.add_argument(
        '--to_json', help='Path to yaml file to convert to json')
    conversion_parser.add_argument(
        '--to_yaml', help='Path to json file to convert to yaml')
    conversion_parser.set_defaults(func=convert)

    return parser.parse_args()


def generate_template(args: argparse.Namespace):
    schemas_dir = os.path.abspath(args.schemas_dir)
    schema_paths = [os.path.join(schemas_dir, path)
                    for path in os.listdir(schemas_dir)]
    ShippingManifest.from_json(
        args.manifest_file, schema_paths).to_excel(args.out_file)


def validate_template(args: argparse.Namespace):
    # TODO: call validation module
    pass


def convert(args: argparse.Namespace):
    if args.to_json:
        json_file = util.yaml_to_json(args.to_json)
        print(f'Wrote {args.to_json} as json to {json_file}')
    elif args.to_yaml:
        yaml_file = util.json_to_yaml(args.to_yaml)
        print(f'Wrote {args.to_yaml} as yaml to {yaml_file}')


if __name__ == '__main__':
    main()
