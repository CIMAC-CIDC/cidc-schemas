# Schemas

CIDC Meta-Data Schemas

# Create template for manifest

###### 1) clone repository
`git clone THIS-REPO`

###### 2) create virtual environment
```bash
virtualenv ENV-NAME
. ENV-NAME/bin/activate
cd schemas
```

###### 3) install dependencies
`pip install -r requirements.txt`

###### 3) Run the script
`python src/create_template.py -y manifest/pbmc.yaml -o $PWD`
