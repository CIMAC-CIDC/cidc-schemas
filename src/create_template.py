##todo 1) Format Shipping address columns 
import yaml
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell,xl_range
import sys
import yaml
import os
import argparse


YAML_PATH = os.path.join(os.path.dirname(__file__), '../', 'schemas')

FORMAT1 = {
'border': 1,
'bg_color': '#C6EFCE',
'bold': True,
'align': 'center',
'valign': 'vcenter',
'indent': 1,
'font_size' : 20
}
FORMAT2 = {
'border': 1,
'bg_color': '#5fa3f0',
'bold': True,
'align': 'center',
'text_wrap': True,
'valign': 'vcenter',
'indent': 1,
}
FORMAT3 = {
'border': 1,
'bg_color': '#b2d2f6',
'bold': True,
'align': 'center',
'text_wrap': True,
'valign': 'vcenter',
'indent': 1,
}
FORMAT4 = {
'border': 1,
'bg_color': '#ffffb3',
'bold': True,
'align': 'center',
'text_wrap': True,
'valign': 'vcenter',
'indent': 1,
}
FORMAT5 = {
'border': 1,
'bg_color': '#b2d2f6',
'bold': True,
'align': 'center',
'text_wrap': True,
'valign': 'vcenter',
'indent': 1,
'font_size' : 20
}

# Load Schma from YAML
def load_schema(file_name):
	with open(file_name, 'r') as stream:
		schema = yaml.load(stream)
	return (schema)

def interface():
    parser = argparse.ArgumentParser(description='Create shipping manifest from yaml file')
    parser.add_argument('-y', '--yaml_file', help='Yaml', required=True)
    parser.add_argument('-o', '--out_dir', help='Yaml', required=True)
    parser = parser.parse_args()
    return parser

def load_schema(file_name):
    with open(file_name, 'r') as stream:
        schema = yaml.load(stream)
    return (schema)

def get_schema_enum(entity, property_id):
    schema = load_schema(os.path.join(YAML_PATH, entity+'.yaml'))
    try:
        des = schema['properties'][property_id]['description']
    except KeyError:
        des = ''
    if 'enum' in schema['properties'][property_id]:
        return des, schema['properties'][property_id]['enum']
    else :
         return des, []

def generate_template(args):
    manifest = load_schema(args.yaml_file)
    manifest_file = manifest['id'] + '.xlsx'
    out_file = os.path.join(args.out_dir, manifest['id'] + '.xlsx')

    workbook = xlsxwriter.Workbook(out_file)
    worksheet = workbook.add_worksheet()

    header_format = workbook.add_format(FORMAT1)
    data_format = workbook.add_format(FORMAT2)
    core_format = workbook.add_format(FORMAT3)
    receiving_format = workbook.add_format(FORMAT4)
    format_5 = workbook.add_format(FORMAT5)

    #Format cell size
    worksheet.set_row(0, 36)
    worksheet.set_column('A:Z', 30)

    # Start from the first cell. Rows and columns are zero indexed.
    row = 0
    col = 0

    # Write the manifest type
    worksheet.merge_range('A1:E1',  manifest['title'].upper(),header_format)
    
    row = row+2

    # Iterate over the core data and write it out row by row.
    for core_entity in manifest['core_columns']:
        enum = []
        column = core_entity.split('.')[1].upper()
        
        #gets the enums for the dropdown. 
        des, enum = get_schema_enum( core_entity.split('.')[0],  core_entity.split('.')[1])

        cell_key = xl_rowcol_to_cell(row, col)
        cell_val = xl_rowcol_to_cell(row, col + 1)
        for i in range(0,5):
            worksheet.write_blank(row, col+i, '' , core_format)

        worksheet.write(cell_key, column + ":", core_format)
        # add dropdowns
        if len(enum) > 0:
            worksheet.data_validation(cell_val, {'validate': 'list',
                                    'source': enum})
        row += 1
    row += 3

    #write data columns
    col = 0
    worksheet.set_row(row-2, 36)
    data_col_range = xl_range(row-2, col, row-2, col + len(manifest['data_columns']) - 1)
    worksheet.merge_range(data_col_range, 'To be filled by Biorepository',format_5)

    recieving_col_range = xl_range(row-2, col + len(manifest['data_columns']), row-2, len(manifest['data_columns']) + len(manifest['receiving_columns'])-1)
    worksheet.merge_range(recieving_col_range, 'To be filled by CIMAC lab',format_5)


    for data_entity in manifest['data_columns']:
        enum = []
        column = data_entity.split('.')[1].upper()
        des, enum = get_schema_enum(data_entity.split('.')[0], data_entity.split('.')[1])
        cell_des = xl_rowcol_to_cell(row-1, col)
        cell_key = xl_rowcol_to_cell(row, col)
        cell_range = xl_range(row+1, col, row+200, col)
        worksheet.write(cell_des, des, data_format)
        worksheet.write(cell_key, column, data_format)
        if len(enum) > 0 :
            worksheet.data_validation(cell_range, {'validate': 'list',
                                    'source': enum})
        col += 1

    for data_entity in manifest['receiving_columns']:
        enum = []
        column = data_entity.split('.')[1].upper()
        des, enum = get_schema_enum(data_entity.split('.')[0], data_entity.split('.')[1])
        cell_des = xl_rowcol_to_cell(row-1, col)
        cell_key = xl_rowcol_to_cell(row, col)
        cell_range = xl_range(row+1, col, row+200, col)
        worksheet.write(cell_des, des, receiving_format)
        worksheet.write(cell_key, column, receiving_format)
        if len(enum) > 0 :
            worksheet.data_validation(cell_range, {'validate': 'list',
                                    'source': enum})
        col += 1
    row += 1

    row += 1
    
    #close the workbook
    workbook.close()

if __name__ == '__main__':
    args = interface()
    generate_template(args)

    