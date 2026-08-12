import json
import os

from ensemble_compilation.graph_representation import SchemaGraph, Table


TPCH_TABLE_ATTRIBUTES = {
    "region": ["r_regionkey", "r_name", "r_comment"],
    "nation": ["n_nationkey", "n_name", "n_regionkey", "n_comment"],
    "supplier": [
        "s_suppkey",
        "s_name",
        "s_address",
        "s_nationkey",
        "s_phone",
        "s_acctbal",
        "s_comment",
    ],
    "customer": [
        "c_custkey",
        "c_name",
        "c_address",
        "c_nationkey",
        "c_phone",
        "c_acctbal",
        "c_mktsegment",
        "c_comment",
    ],
    "part": [
        "p_partkey",
        "p_name",
        "p_mfgr",
        "p_brand",
        "p_type",
        "p_size",
        "p_container",
        "p_retailprice",
        "p_comment",
    ],
    "partsupp": [
        "ps_partkey",
        "ps_suppkey",
        "ps_availqty",
        "ps_supplycost",
        "ps_comment",
    ],
    "orders": [
        "o_orderkey",
        "o_custkey",
        "o_orderstatus",
        "o_totalprice",
        "o_orderdate",
        "o_orderpriority",
        "o_clerk",
        "o_shippriority",
        "o_comment",
    ],
    "lineitem": [
        "l_orderkey",
        "l_partkey",
        "l_suppkey",
        "l_linenumber",
        "l_quantity",
        "l_extendedprice",
        "l_discount",
        "l_tax",
        "l_returnflag",
        "l_linestatus",
        "l_shipdate",
        "l_commitdate",
        "l_receiptdate",
        "l_shipinstruct",
        "l_shipmode",
        "l_comment",
    ],
}


TPCH_PRIMARY_KEYS = {
    "region": ["r_regionkey"],
    "nation": ["n_nationkey"],
    "supplier": ["s_suppkey"],
    "customer": ["c_custkey"],
    "part": ["p_partkey"],
    "partsupp": ["ps_partkey", "ps_suppkey"],
    "orders": ["o_orderkey"],
    "lineitem": ["l_orderkey", "l_linenumber"],
}


TPCH_DEFAULT_TABLE_SIZES = {
    "region": 5,
    "nation": 25,
    "supplier": 10000,
    "customer": 150000,
    "part": 200000,
    "partsupp": 800000,
    "orders": 1500000,
    "lineitem": 6001215,
}


def _csv_root_from_template(csv_path):
    marker = "{}.csv"
    if marker in csv_path:
        return os.path.dirname(csv_path.replace(marker, "placeholder.csv"))
    return os.path.dirname(csv_path)


def _load_table_sizes(csv_path):
    root = _csv_root_from_template(csv_path)
    row_counts_path = os.path.join(root, "row_counts.json")
    if not os.path.exists(row_counts_path):
        return dict(TPCH_DEFAULT_TABLE_SIZES)
    with open(row_counts_path, "r", encoding="utf-8") as handle:
        row_counts = json.load(handle)
    sizes = dict(TPCH_DEFAULT_TABLE_SIZES)
    for table in TPCH_TABLE_ATTRIBUTES:
        if table in row_counts:
            sizes[table] = int(row_counts[table])
    return sizes


def gen_tpch_schema(csv_path):
    schema = SchemaGraph()
    table_sizes = _load_table_sizes(csv_path)

    for table_name, attributes in TPCH_TABLE_ATTRIBUTES.items():
        schema.add_table(
            Table(
                table_name,
                attributes=attributes,
                csv_file_location=csv_path.format(table_name),
                table_size=table_sizes[table_name],
                primary_key=TPCH_PRIMARY_KEYS[table_name],
            )
        )

    schema.add_relationship("orders", "o_custkey", "customer", "c_custkey")
    schema.add_relationship("lineitem", "l_orderkey", "orders", "o_orderkey")
    schema.add_relationship("lineitem", "l_partkey", "part", "p_partkey")
    schema.add_relationship("lineitem", "l_suppkey", "supplier", "s_suppkey")
    schema.add_relationship("supplier", "s_nationkey", "nation", "n_nationkey")
    schema.add_relationship("customer", "c_nationkey", "nation", "n_nationkey")
    schema.add_relationship("nation", "n_regionkey", "region", "r_regionkey")
    schema.add_relationship("partsupp", "ps_partkey", "part", "p_partkey")
    schema.add_relationship("partsupp", "ps_suppkey", "supplier", "s_suppkey")

    return schema


def gen_tpch_sf1_schema(csv_path):
    return gen_tpch_schema(csv_path)


def gen_tpch_sf10_schema(csv_path):
    return gen_tpch_schema(csv_path)


def gen_tpch_sf100_schema(csv_path):
    return gen_tpch_schema(csv_path)


def gen_tpch_sf0_1_schema(csv_path):
    return gen_tpch_schema(csv_path)


def gen_tpch_sf0_01_schema(csv_path):
    return gen_tpch_schema(csv_path)
