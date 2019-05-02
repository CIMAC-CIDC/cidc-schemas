##todo 1) Format Shipping address columns 
import yaml
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell,xl_range
from datetime import date, time
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
def load_schema():
    schema_all = {}
    for yaml_file in os.listdir(YAML_PATH):
        with open(os.path.join(YAML_PATH,yaml_file), 'r') as stream:
            schema = yaml.load(stream)
            schema_all[schema['id']] = schema
    return schema_all

def load_manifest(file_name):
	with open(file_name, 'r') as stream:
		schema = yaml.load(stream)
	return (schema)

def interface():
    parser = argparse.ArgumentParser(description='Create shipping manifest from yaml file')
    parser.add_argument('-y', '--yaml_file', help='Yaml', required=True)
    parser.add_argument('-o', '--out_dir', help='Yaml', required=True)
    parser = parser.parse_args()
    return parser


def get_schema_des(schema, property_id):
    try:
        des = schema['properties'][property_id]['description']
    except KeyError:
        des = ''
    return des

def get_schema_enum(schema, property_id):
    try:
        enum = schema['properties'][property_id]['enum']
    except KeyError:
        enum = []
    return enum

def get_schema_format(schema, property_id):
    try:
        d_format = schema['properties'][property_id]['format']
    except KeyError:
        d_format = ''
    return d_format

def generate_template(args):
    schema_all = load_schema()
    manifest = load_manifest(args.yaml_file)
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

        column = core_entity.split('.')[1].upper()
        des, enum, d_format = get_data(core_entity, schema_all)

        cell_key = xl_rowcol_to_cell(row, col)
        cell_val = xl_rowcol_to_cell(row, col + 1)
        for i in range(0,5):
            worksheet.write_blank(row, col+i, '' , core_format)

        worksheet.write(cell_key, column + ":", core_format)
        # add dropdowns and datetime checks
        if len(enum) > 0:
            worksheet.data_validation(cell_val, {'validate': 'list', 'source': enum})
        elif d_format == 'date':
            validation_string = get_date_validation_str(cell_val)
            worksheet.data_validation(cell_val, {'validate': 'custom', 'value': validation_string,'error_message':'Please enter date in format mm/dd/yyyy'})
        elif d_format == 'time':
            worksheet.data_validation(cell_val, {'validate': 'time','criteria': 'between','minimum': time(0, 0),'maximum': time(23, 59),
            'error_message':'Please enter time in format hh:mm'})
        row += 1
    row += 3

    #write data columns
    col = 0
    worksheet.set_row(row-2, 36)
    data_col_range = xl_range(row-2, col, row-2, col + len(manifest['shipping_columns']) - 1)
    worksheet.merge_range(data_col_range, 'To be filled by Biorepository',format_5)

    recieving_col_range = xl_range(row-2, col + len(manifest['shipping_columns']), row-2, len(manifest['shipping_columns']) + len(manifest['receiving_columns'])-1)
    worksheet.merge_range(recieving_col_range, 'To be filled by CIMAC lab',format_5)


    for data_entity in manifest['shipping_columns']:
        column = data_entity.split('.')[1].upper()
        des, enum, d_format = get_data(data_entity, schema_all)
        
        cell_des = xl_rowcol_to_cell(row-1, col)
        cell_key = xl_rowcol_to_cell(row, col)
        cell_range = xl_range(row+1, col, row+200, col)
        
        worksheet.write(cell_des, des, data_format)
        worksheet.write(cell_key, column, data_format)
        
        if len(enum) > 0 :
            worksheet.data_validation(cell_range, {'validate': 'list',
                                    'source': enum})
        elif d_format == 'date':
            validation_string = get_date_validation_str(cell_range)
            worksheet.data_validation(cell_range, {'validate': 'custom', 'value': validation_string,'error_message':'Please enter date in format mm/dd/yyyy'})
        elif d_format == 'time':
            worksheet.data_validation(cell_range, {'validate': 'time','criteria': 'between','minimum': time(0, 0),'maximum': time(23, 59),
            'error_message':'Please enter time in format hh:mm'})
        col += 1

    for data_entity in manifest['receiving_columns']:
        enum = []
        column = data_entity.split('.')[1].upper()
        des, enum, d_format = get_data(data_entity, schema_all)
        cell_des = xl_rowcol_to_cell(row-1, col)
        cell_key = xl_rowcol_to_cell(row, col)
        cell_range = xl_range(row+1, col, row+200, col)
        worksheet.write(cell_des, des, receiving_format)
        worksheet.write(cell_key, column, receiving_format)
        if len(enum) > 0 :
            worksheet.data_validation(cell_range, {'validate': 'list',
                                    'source': enum})
        elif d_format == 'date':
            validation_string = get_date_validation_str(cell_range)
            worksheet.data_validation(cell_range, {'validate': 'custom', 'value': validation_string, 'error_message':'Please enter date in format mm/dd/yyyy'})
        elif d_format == 'time':
            worksheet.data_validation(cell_range, {'validate': 'time','criteria': 'between','minimum': time(0, 0),'maximum': time(23, 59),
            'error_message':'Please enter time in format hh:mm'})
        col += 1
    row += 1

    row += 1   

    #close the workbook
    workbook.close()

def get_data(data_entity, schema_all):
    entity = schema_all[data_entity.split('.')[0]]
    property_id = data_entity.split('.')[1]
    des = get_schema_des(entity,  property_id)
    enum = get_schema_enum(entity,  property_id)
    d_format = get_schema_format(entity,  property_id)
    return des, enum, d_format

def get_date_validation_str(cell):
    return  '=AND(ISNUMBER(%s),LEFT(CELL("format",%s),1)="D")' %(cell, cell)


if __name__ == '__main__':
    args = interface()
    generate_template(args)

