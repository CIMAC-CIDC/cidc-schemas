import yaml
import xlsxwriter
import sys
import os
from cerberus import Validator

# Remaining todos
# 1. Order columns by the order attribute
# 2. For those columns that have "allowed" attribute, restrict by pull-down menu

# Load Schma from YAML
def load_schema(file_name):
	with open(file_name, 'r') as stream:
		schema = yaml.load(stream)
	return (schema)

# Write Templated Excel Spreadsheet
def write_excel(file_name, schema, schema_name):
	workbook = xlsxwriter.Workbook(file_name)
	write_tab(workbook ,"Global", schema, schema_name+".global", 1, "green")
	write_tab(workbook ,"Data", schema, schema_name+".data", 2, "red")
	workbook.close()

# Write One Tab within Templated Excel Spreadsheet
def write_tab(workbook, tab_name, schema, schema_name, type, color):
	worksheet = workbook.add_worksheet(tab_name)
	worksheet.set_tab_color(color)
	field_names = schema[schema_name]
	col = 0

	header = workbook.add_format({'bold': True, 'bg_color': '#dddddd'})
	for field_name in field_names:
		worksheet.write(0, col, field_names[field_name]["human_label"], header)
		worksheet.write(1, col, field_name, header)
		worksheet.set_column(col, col, 25)
		if type == 1:
			worksheet.write(2, col, "[Please complete one row]")
		else:
			worksheet.write(2, col, "[Please complete rows]")
			worksheet.write(3, col, "[Please complete rows]")
		col+= 1

schema_yaml = sys.argv[1]
path, schema_name = os.path.split(schema_yaml)
schema_name = schema_name.replace(".yaml", "")
print ("Schema Name:  %s" % schema_name)
schema = load_schema(schema_yaml)
excel_name = schema_name + ".xlsx"
print ("Reading Schema from:  %s" % schema_yaml)
print ("Writing Excel Template to:  %s" % excel_name)
write_excel(excel_name, schema, schema_name)

# Try out cerberus validator
field_names = schema[schema_name+".data"]

# Drop fields that are not part of cerberus
# Otherwise, you get cerberus loading errors
for field in field_names:
	field_names[field].pop('description', None)
	field_names[field].pop('human_label', None)
	field_names[field].pop('order', None)

v = Validator(schema[schema_name+".data"])

# This should fail...
document = {'patient.site_patient_id': 'john doe',
	'sample.tissue_collection_date': 'hello'}