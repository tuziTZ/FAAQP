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
from itertools import combinations

flights_storage_cost = 413 * 20 #原始数据占用的存储单位
flights_rspn_storage_cost = 16 #RSPN模型自身占用的开销
budget_ratio = 0.1 # 存储比例
storage_budget = (flights_storage_cost * budget_ratio - flights_rspn_storage_cost)  * 1024 * 1024 #可用字节数
leaf_list = {} #乘积节点对应的叶子节点列表
size_limit = 5

#广度遍历SPN，对每个乘积节点，找到叶节点，保存到leaf_list中
def find_leaf(node):
    global leaf_list
    if isinstance(node, Product):
        leaf_list[node] = []
        for n in node.children:
            if isinstance(n, IdentityNumericLeaf) or isinstance(n, Categorical):
                leaf_list[node].append(n)

#对每个叶子结点，计算节点数据所占存储，节点数值分布的标准差
def get_node_size_std():
    node_size, node_std = {}, {}
    for p_node, c_nodes in leaf_list.items():
        if c_nodes:
            for i in range(len(c_nodes)):
                i_node = c_nodes[i]
                temp_tuples = []
                size = 0
                for i_key, i_values in i_node.unique_vals_ids.items():
                    temp_tuples += [i_key] * len(i_values)
                    size += i_values.__sizeof__()
                if isinstance(i_node, IdentityNumericLeaf):
                    node_std[i_node] = np.std(temp_tuples)
                node_size[i_node] = size
    return node_size, node_std

# 核心函数
def storage_control(ensemble_location, ensemble_path):
    spn_ensemble = read_ensemble(ensemble_location, build_reverse_dict=True)

    for spn in spn_ensemble.spns:
        bfs(spn.mspn, find_leaf)

    node_size, node_std = get_node_size_std()

    start_t = perf_counter()
    node_weight_value = {}
    max_mean, max_sum, max_std = 0, 0, 0
    for p_node, c_nodes in leaf_list.items():
        if c_nodes:
            for i in range(len(c_nodes)):
                i_node = c_nodes[i]
                for j in range(i + 1, len(c_nodes)):
                    j_node = c_nodes[j]
                    temp_errors = []
                    for i_key, i_values in i_node.unique_vals_ids.items():
                        for j_key, j_values in j_node.unique_vals_ids.items():
                            independent = len(i_values) * len(j_values) / i_node.cardinality
                            exact = len(i_values & j_values)
                            abs_error = abs(exact - independent)
                            temp_errors.append(abs_error)
                    if max_mean < np.mean(temp_errors):
                        max_mean = np.mean(temp_errors)
                    if max_sum < sum(temp_errors):
                        max_sum = sum(temp_errors)
                    node_weight_value[(i_node, j_node)] = [node_size[i_node] + node_size[j_node], np.mean(temp_errors), sum(temp_errors)]
                    if isinstance(i_node, IdentityNumericLeaf):
                        node_weight_value[(i_node, j_node)].append(node_std[i_node])
                        print(max_std, node_std[i_node])
                        if max_std < node_std[i_node]:
                            max_std = node_std[i_node]
                    else:
                        node_weight_value[(i_node, j_node)].append(0)

                    if isinstance(j_node, IdentityNumericLeaf):
                        node_weight_value[(i_node, j_node)].append(node_std[j_node])
                        print(max_std, node_std[j_node])
                        if max_std < node_std[j_node]:
                            max_std = node_std[j_node]
                    else:
                        node_weight_value[(i_node, j_node)].append(0)

    print('node_weight_value:', len(node_weight_value))
    print(max_std, max_sum, max_mean)

    for key, values in node_weight_value.items():
        v = 0
        if max_std !=0 and max_sum != 0 and max_mean != 0:
            v = (values[1] / max_mean + values[2] / max_sum) / 4 + (values[3] / max_std + values[4] / max_std) / 4
        elif max_sum != 0 and max_mean != 0:
            v = (values[1] / max_mean + values[2] / max_sum) / 2

        node_weight_value[key] = [values[0], v]

    print(perf_counter() - start_t)
    # 卡在这了
    # storage_package_list = optimal(node_weight_value, node_size)
    storage_package_list = greedy(node_weight_value, node_size)

    print(perf_counter() - start_t)

    print('storage_package_list:', len(storage_package_list))

    for p_node, c_nodes in leaf_list.items():
        if c_nodes:
            for node in c_nodes:
                if node not in storage_package_list:
                    node.unique_vals_ids.clear()

    end_t = perf_counter()
    print(end_t - start_t)
    spn_ensemble.save(ensemble_path)


def greedy(node_weight_value, node_size):
    temp = max(node_weight_value.items(), key=lambda item: item[1][1] / item[1][0])
    current_storage_cost, current_value = 0, 0
    storage_package_list = []
    storage_package_pair = []

    while current_storage_cost < storage_budget:
        if len(storage_package_pair) >= size_limit:
            break
        if current_storage_cost + node_weight_value[temp[0]][0] < storage_budget and temp[
            0] not in storage_package_pair:
            current_storage_cost += node_weight_value[temp[0]][0]
            current_value += node_weight_value[temp[0]][1]
            storage_package_pair.append(temp[0])
            del node_weight_value[temp[0]]

            if temp[0][0] not in storage_package_list:
                for node in storage_package_list:
                    if (node, temp[0][0]) in node_weight_value.keys():
                        storage_package_pair.append((node, temp[0][0]))
                        current_value += node_weight_value[(node, temp[0][0])][1]
                        del node_weight_value[(node, temp[0][0])]
                    if (temp[0][0], node) in node_weight_value.keys():
                        storage_package_pair.append((temp[0][0], node))
                        current_value += node_weight_value[(temp[0][0], node)][1]
                        del node_weight_value[(temp[0][0], node)]
                storage_package_list.append(temp[0][0])
                update_reduce_size(node_weight_value, node_size, temp[0][0])

            if temp[0][1] not in storage_package_list:
                for node in storage_package_list:
                    if (node, temp[0][1]) in node_weight_value.keys():
                        storage_package_pair.append((node, temp[0][1]))
                        current_value += node_weight_value[(node, temp[0][1])][1]
                        del node_weight_value[(node, temp[0][1])]
                    if (temp[0][1], node) in node_weight_value.keys():
                        storage_package_pair.append((temp[0][1], node))
                        current_value += node_weight_value[(temp[0][1], node)][1]
                        del node_weight_value[(temp[0][1], node)]
                storage_package_list.append(temp[0][1])
                update_reduce_size(node_weight_value, node_size, temp[0][1])
            temp = max(node_weight_value.items(), key=lambda item: item[1][1] / item[1][0])
        elif current_storage_cost + node_weight_value[temp[0]][0] > storage_budget:
            break

    print('storage_package_pair:', len(set(storage_package_pair)))
    print('greedy:', current_storage_cost, current_value)
    return storage_package_list

#枚举组合找最大值。。。
def optimal(node_weight_value, node_size):
    current_storage_cost, current_value = 0, 0
    storage_package_list = []
    storage_package_pair = []
    start_t = perf_counter()
    pair_combs = combinations(node_weight_value.keys(), size_limit)
    max_u = -10000
    opt_pair = None
    for pair in pair_combs:
        u = 0
        for item in pair:
            u += node_weight_value[item][1]
        if u > max_u:
            max_u = u
            opt_pair = pair
    end_t = perf_counter()
    print(end_t - start_t)
    print("max_u:", max_u)


def greedy_CELF(node_weight_value, node_size):
    current_storage_cost, current_value = 0, 0
    storage_package_list = []
    storage_package_pair = []
    for key, values in node_weight_value.items():
        if key not in storage_package_pair:
            current_storage_cost += values[0]
            current_value += values[1]
            storage_package_pair.append(key)

            if key[0] not in storage_package_list:
                for node in storage_package_list:
                    if (node, key[0]) in node_weight_value.keys():
                        storage_package_pair.append((node, key[0]))
                        current_value += node_weight_value[(node, key[0])][1]
                    if (key[0], node) in node_weight_value.keys():
                        storage_package_pair.append((key[0], node))
                        current_value += node_weight_value[(key[0], node)][1]
                storage_package_list.append(key[0])
                update_reduce_size(node_weight_value, node_size, key[0])

            if key[1] not in storage_package_list:
                for node in storage_package_list:
                    if (node, key[1]) in node_weight_value.keys():
                        storage_package_pair.append((node, key[1]))
                        current_value += node_weight_value[(node, key[1])][1]
                    if (key[1], node) in node_weight_value.keys():
                        storage_package_pair.append((key[1], node))
                        current_value += node_weight_value[(key[1], node)][1]
                storage_package_list.append(key[1])
                update_reduce_size(node_weight_value, node_size, key[1])

            if current_storage_cost > storage_budget:
                minimum_size = current_storage_cost - storage_budget
                max_value, pop_pair = 0, None
                for nodes in storage_package_pair:
                    if node_size[nodes[0]] + node_size[nodes[1]] >= minimum_size:
                        reduce_value = get_reduce_value(node_weight_value, storage_package_pair, nodes[0], nodes[1])
                        if max_value < current_value - reduce_value:
                            max_value = current_value - reduce_value
                            pop_pair = nodes

                storage_package_pair.remove(pop_pair)
                current_storage_cost -= node_size[pop_pair[0]] + node_size[pop_pair[1]]
                current_value = max_value
                if pop_pair[0] in storage_package_list:
                    storage_package_list.remove(pop_pair[0])
                elif pop_pair[1] in storage_package_list:
                    storage_package_list.remove(pop_pair[1])
                update_increase_size(node_weight_value, node_size, pop_pair[0])
                update_increase_size(node_weight_value, node_size, pop_pair[1])
    print('storage_package_pair:', len(set(storage_package_pair)))
    print('greedy_celf:', current_storage_cost, current_value)
    return storage_package_list


def get_reduce_value(node_weight_value, storage_package_pair, node_1, node_2):
    value = 0
    for nodes in storage_package_pair:
        if node_1 in nodes or node_2 in nodes:
            value += node_weight_value[nodes][1]
    return value


def update_reduce_size(node_weight_value, node_size, node):
    for key, values in node_weight_value.items():
        if key[0] == node or key[1] == node:
            node_weight_value[key][0] -= node_size[node]


def update_increase_size(node_weight_value, node_size, node):
    for key, values in node_weight_value.items():
        if key[0] == node or key[1] == node:
            node_weight_value[key][0] += node_size[node]

# 输入训练好的模型
input_path = "./flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_RoaringBitmap.pkl"
output_path = "./flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_budget.pkl"
storage_budget = 0.1  # 占原数据 10%

ensemble_location = input_path
ensemble_path = output_path
storage_control(ensemble_location, ensemble_path)

