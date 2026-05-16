from ensemble_compilation.graph_representation import SchemaGraph, Table


def gen_dom1000_1M_schema(csv_path):
    """
    cs schema with 1M tuples
    """

    schema = SchemaGraph()
    schema.add_table(Table('s10c00',
                           attributes=['col0', 'col1'],
                           csv_file_location=csv_path.format('skew1.0_corr0.0'),
                           table_size=10000000, primary_key=[''], sample_rate=0.1
                           ))

    return schema


def gen_dom1000_schema(csv_path):
    schema = gen_dom1000_1M_schema(csv_path)

    schema.table_dictionary['s10c00'].sample_rate = 1
    schema.table_dictionary['s10c00'].table_size = 1000000
    schema.table_dictionary['s10c00'].csv_file_location = csv_path.format('skew1.0_corr0.0')

    return schema


def gen_c00s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c00s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.0s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c02s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c02s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.2s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c04s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c04s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.4s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c04s00_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c04s00',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.4s0.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema

def gen_c04s05_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c04s05',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.4s0.5'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c04s15_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c04s15',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.4s1.5'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema

def gen_c04s20_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c04s20',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.4s2.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))

    return schema


def gen_c06s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c06s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.6s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c08s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c08s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c0.8s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema


def gen_c10s10_schema(csv_path):
    schema = SchemaGraph()
    schema.add_table(Table('c10s10',
                           attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9'],
                           csv_file_location=csv_path.format('c1.0s1.0'),
                           table_size=1000000, primary_key=[''], sample_rate=1
                           ))
    return schema