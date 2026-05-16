import csv
import logging
import pickle
from enum import Enum
from time import perf_counter, sleep
import numpy as np
import pandas as pd
import math
import copy
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from ensemble_compilation.graph_representation import Query, QueryType, AggregationType, AggregationOperationType
from ensemble_compilation.physical_db import DBConnection
from ensemble_compilation.spn_ensemble import read_ensemble
from evaluation.utils import parse_query, save_csv
from spn.structure.Base import bfs
from spn.structure.Base import Product
from rspn.structure.base import Sum
from rspn.structure.leaves import identity_expectation_ids, identity_likelihood_range_ids, categorical_likelihood_range_ids
from rspn.structure.leaves import Categorical, IdentityNumericLeaf
from schemas.ssb.schema import gen_500gb_ssb_schema, gen_sf50_ssb_schema
from roaringbitmap import RoaringBitmap

leaf_dict = {}

def leaf_list_initial(node):
    global leaf_dict
    if not isinstance(node, Product) and not isinstance(node, Sum):
        if node.scope[0] in leaf_dict:
            leaf_dict[node.scope[0]].append(node)
        else:
            leaf_dict[node.scope[0]] = [node]


def get_leaf(ensemble_location):
    spn_ensemble = read_ensemble(ensemble_location, build_reverse_dict=True)
    for spn in spn_ensemble.spns:
        bfs(spn.mspn, leaf_list_initial)


def node_p(node, evidence, node_likelihoods):
    temp_ranges = set(evidence[0])
    temp_ranges.remove(None)
    if len(temp_ranges) > 1:
        if isinstance(node, IdentityNumericLeaf):
            temp = identity_likelihood_range_ids(node, evidence)
        elif isinstance(node, Categorical):
            temp = categorical_likelihood_range_ids(node, evidence)
        return temp[0].item(), temp[1], temp[2]
    else:
        temp = node_likelihoods[type(node)](node, evidence)
        return temp.item(), [None], False


def leaf_calculation(relevant_scope, evidence, node_likelihoods):
    global leaf_dict
    node_results = {}
    for key, value in leaf_dict.items():
        if key in relevant_scope:
            for node in value:
                node_results[node] = node_p(node, evidence, node_likelihoods)
    return node_results


def group_by_split(ensemble_location='/home/qym/zhb/ssb-benchmark/spn_ensembles/ensemble_single_ssb-50gb_100000_RoaringBitmap.pkl',
                   query_filename='./benchmarks/ssb/sql/aqp_queries.sql'):
    spn_ensemble = read_ensemble(ensemble_location, build_reverse_dict=True)
    table_csv_path= '../ssb-benchmark/{}.csv'
    schema = gen_sf50_ssb_schema(table_csv_path)
    queries = ["select d_year, s_city, p_brand1, sum(lo_revenue) - sum(lo_supplycost) from dwdate, customer, supplier, part, lineorder where lo_custkey = c_custkey and lo_suppkey = s_suppkey and lo_partkey = p_partkey and lo_orderdate = d_datekey and c_region = 'AMERICA' and s_nation = 'UNITED STATES' and d_year >= 1997 and d_year <= 1998 and p_category = 'MFGR#14' group by d_year, s_city, p_brand1 order by d_year, s_city, p_brand1;"]
    q = "select sum(lo_revenue) - sum(lo_supplycost) from dwdate, customer, supplier, part, lineorder where lo_custkey = c_custkey and lo_suppkey = s_suppkey and lo_partkey = p_partkey and lo_orderdate = d_datekey and c_region = 'AMERICA' and s_nation = 'UNITED STATES' and d_year >= 1997 and d_year <= 1998 and p_category = 'MFGR#14'"
    q_list = []
    for query_no, query_str in enumerate(queries):
        print(query_str)
        query_str = query_str.strip()
        query = parse_query(query_str.strip(), schema)
        if len(query.group_bys) > 0:
            group_bys_scopes, result_tuples, result_tuples_translated = spn_ensemble._evaluate_group_by_spn_ensembles(query)
            for i in range(len(result_tuples_translated)):
                temp_q = q
                for group_by_idx, (table, attribute) in enumerate(query.group_bys):
                    if isinstance(result_tuples_translated[i][group_by_idx], float):
                        condition = attribute + ' = ' + str(int(result_tuples_translated[i][group_by_idx]))
                    else:
                        condition = attribute + " = '" + result_tuples_translated[i][group_by_idx] + "'"
                    temp_q = temp_q + ' and ' + condition
                q_list.append(temp_q+';\n')
    with open('./benchmarks/ssb/sql/ssb12_queries.sql', 'w') as f:
        f.writelines(q_list)
        f.close()


def id_process(i_l):
    l = []
    for i in range(len(i_l)):
        temp = RoaringBitmap()
        for j in i_l[i]:
            temp |= j
        l.append(temp)
    return l

def id_process2(i_l):
    for i in range(10):
        id_process(i_l)


from array import array


class BitMap:
    def __init__(self):
        self.n = 5
        self.bitsize = 1 << self.n
        self.typecode = 'I' 
        self.lowerbound = 0  

    @staticmethod
    def greater_power2n(x):
        i = 1
        while True:
            y = x >> i
            x |= y
            if y == 0:
                break
            i <<= 1
        return x + 1

    def load(self, inp):
        maxi = max(inp)
        num_arr = max(self.greater_power2n(maxi) >> self.n, 1)  
        self.arr = array(self.typecode, [0] * num_arr)
        for x in inp:
            self._set(x)

    def _set(self, x, set_val=True):
        arr_idx = x >> self.n  
        bit_idx = x & (self.bitsize - 1)  
        if set_val:
            self.arr[arr_idx] |= 1 << bit_idx
        else:
            self.arr[arr_idx] &= ~(1 << bit_idx)
