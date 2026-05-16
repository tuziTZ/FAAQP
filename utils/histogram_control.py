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
from roaringbitmap import RoaringBitmap
from rspn.structure.leaves import Categorical, IdentityNumericLeaf


leaf_list = {}

def find_leaf(node):
    global leaf_list
    if isinstance(node, Product):
        leaf_list[node] = []
        for n in node.children:
            if isinstance(n, IdentityNumericLeaf) or isinstance(n, Categorical):
                leaf_list[node].append(n)


leaf_list_2 = {}
def find_leaf_2(node):
    global leaf_list_2
    if isinstance(node, Product):
        leaf_list_2[node] = []
        for n in node.children:
            if isinstance(n, IdentityNumericLeaf):
                leaf_list_2[node].append(n)


def histogram_control(ensemble_location, ensemble_path, threshold=10):
    spn_ensemble = read_ensemble(ensemble_location, build_reverse_dict=True)
    start_t = perf_counter()
    for spn in spn_ensemble.spns:
        bfs(spn.mspn, find_leaf)
    for p_node, c_nodes in leaf_list.items():
        node_max_error = {}
        if c_nodes:
            rdc_adjacency_matrix_dict = None
            for c_node in c_nodes:
                if isinstance(c_node, IdentityNumericLeaf):
                    rdc_adjacency_matrix_dict = c_node.rdc_adjacency_matrix_dict
                    break
            if True:
                for i in range(len(c_nodes)):
                    i_node = c_nodes[i]
                    if isinstance(i_node, IdentityNumericLeaf):
                        if i_node not in node_max_error.keys():
                            node_max_error[i_node] = {}
                        for j in range(i + 1, len(c_nodes)):
                            j_node = c_nodes[j]
                            for i_key, i_values in i_node.unique_vals_ids.items():
                                for j_key, j_values in j_node.unique_vals_ids.items():
                                    independent = len(i_values) * len(j_values) / i_node.cardinality
                                    exact = len(i_values & j_values)
                                    abs_error = abs(exact - independent)
                                    if i_key not in node_max_error[i_node].keys():
                                        node_max_error[i_node][i_key] = abs_error
                                    elif node_max_error[i_node][i_key] < abs_error:
                                        node_max_error[i_node][i_key] = abs_error
                    elif isinstance(i_node, Categorical):
                        for j in range(i + 1, len(c_nodes)):
                            j_node = c_nodes[j]
                            if isinstance(j_node, IdentityNumericLeaf):
                                if j_node not in node_max_error.keys():
                                    node_max_error[j_node] = {}
                                for j_key, j_values in j_node.unique_vals_ids.items():
                                    for i_key, i_values in i_node.unique_vals_ids.items():
                                        independent = len(i_values) * len(j_values) / p_node.cardinality
                                        exact = len(i_values & j_values)
                                        abs_error = abs(exact - independent)
                                        if j_key not in node_max_error[j_node].keys():
                                            node_max_error[j_node][j_key] = abs_error
                                        elif node_max_error[j_node][j_key] < abs_error:
                                            node_max_error[j_node][j_key] = abs_error
        if node_max_error:
            for numeric_node, max_error_dict in node_max_error.items():
                print(numeric_node, len(numeric_node.unique_vals_ids))
                if not max_error_dict:
                    continue
                key_merge, temp_keys = [], []
                sum_error = 0
                temp = RoaringBitmap()
                temp_k = []
                temp_key_porb = []
                for key, max_error in max_error_dict.items():
                    sum_error += max_error
                    if sum_error <= threshold:
                        temp_keys.append(key)
                    elif not temp_keys:
                        key_merge.append(tuple([key]))
                        sum_error = 0
                    else:
                        key_merge.append(tuple(temp_keys))
                        key_merge.append(tuple([key]))
                        temp_keys.clear()
                        sum_error = 0
                if temp_keys:
                    key_merge.append(tuple(temp_keys))
                    temp_keys.clear()
                for keys in key_merge:
                    if len(keys) > 1:
                        bitmap_merge = RoaringBitmap()
                        key_porb = []
                        sum_key = 0
                        for key in keys:
                            bitmap_merge |= numeric_node.unique_vals_ids[key]
                            key_porb.append(len(numeric_node.unique_vals_ids[key]) / numeric_node.cardinality)
                            temp_key_porb.append(len(numeric_node.unique_vals_ids[key]) / numeric_node.cardinality)
                            sum_key += key * len(numeric_node.unique_vals_ids[key])
                            temp_k.append(key)
                            del numeric_node.unique_vals_ids[key]
                        c_b = copy.deepcopy(bitmap_merge | temp)
                        c_p = copy.deepcopy(temp_key_porb)
                        numeric_node.unique_vals_ids[tuple(keys)] = (bitmap_merge, key_porb)
                        numeric_node.unique_vals_ids_average_key[tuple(keys)] = sum_key / len(bitmap_merge)
                        # numeric_node.pre_ids_bitmap[tuple(temp_k)] = (c_b, c_p)
                    else:
                        key = keys[0]
                        temp |= numeric_node.unique_vals_ids[key]
                        temp_k.append(key)
                        temp_key_porb.append(len(numeric_node.unique_vals_ids[key]) / numeric_node.cardinality)
                        c_b = copy.deepcopy(temp)
                        c_p = copy.deepcopy(temp_key_porb)
                        # numeric_node.pre_ids_bitmap[tuple(temp_k)] = (c_b, c_p)
                        # print(numeric_node.scope, tuple(keys))
    end_t = perf_counter()
    print(end_t - start_t)
    spn_ensemble.save(ensemble_path)


def ec_pre(ensemble_location_1, ensemble_location_2):
    spn_ensemble_pre = read_ensemble(ensemble_location_1, build_reverse_dict=True)
    spn_ensemble_ec = read_ensemble(ensemble_location_2, build_reverse_dict=True)
    for spn in spn_ensemble_ec.spns:
        bfs(spn.mspn, find_leaf)
    for spn in spn_ensemble_pre.spns:
        bfs(spn.mspn, find_leaf_2)

# 设置输入输出路径
input_path = "./flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_budget.pkl"
output_path = "./flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_BMS.pkl"
threshold = 100


ensemble_location = input_path
ensemble_path = output_path

histogram_control(ensemble_location, ensemble_path, threshold=100)

