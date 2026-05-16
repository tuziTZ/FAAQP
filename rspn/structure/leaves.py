import numpy as np
import copy
import math
import random
from time import perf_counter
from spn.structure.Base import Leaf
from spn.structure.leaves.parametric.Parametric import Parametric
from roaringbitmap import RoaringBitmap
from multiprocessing.dummy import Pool

class Categorical(Parametric):
    """
    Implements a univariate categorical distribution with k parameters
    """

    from spn.structure.StatisticalTypes import Type
    from collections import namedtuple

    type = Type.CATEGORICAL
    property_type = namedtuple("Categorical", "p")

    def __init__(self, p, null_value, scope, cardinality=0, unique_vals_ids=None):
        Parametric.__init__(self, type(self).type, scope=scope)

        # parameters
        assert np.isclose(np.sum(p), 1), "Probabilities p shall sum to 1"
        if not isinstance(p, np.ndarray):
            p = np.array(p)
        self.p = p
        self.cardinality = cardinality

        self.null_value = null_value
        self.unique_vals_ids = unique_vals_ids

    def copy_node(self):
        return Categorical(np.copy(self.p), self.null_value, self.scope, cardinality=self.cardinality, unique_vals_ids=self.unique_vals_ids)

    @property
    def parameters(self):
        return __class__.property_type(p=self.p)

    @property
    def k(self):
        return len(self.p)

    @property
    def get_ids(self):
        return self.unique_vals_ids

    @property
    def get_specific_id(self, x):
        if x in self.unique_vals_ids.keys():
            return self.unique_vals_ids[x]
        else:
            exit('Group Error: group missing!')


class IdentityNumericLeaf(Leaf):
    def __init__(self, unique_vals, probabilities, null_value, scope, cardinality=0, unique_vals_ids=None,
                 rdc_adjacency_matrix_dict=None):
        """
        Instead of histogram remember individual values.
        :param unique_vals: all possible values in leaf
        :param mean: mean of not null values
        :param inverted_mean: inverted mean of not null values
        :param square_mean: mean of squared not null values
        :param inverted_square_mean: mean of 1/squared not null values
        :param prob_sum: cumulative sum of probabilities
        :param null_value_prob: proportion of null values in the leaf
        :param scope:
        """
        Leaf.__init__(self, scope=scope)
        if not isinstance(unique_vals, np.ndarray):
            unique_vals = np.array(unique_vals)
        self.unique_vals = unique_vals
        self.cardinality = cardinality
        self.null_value = null_value
        self.unique_vals_idx = None
        self.update_unique_vals_idx()
        # self.unique_vals_prob = {}
        self.unique_vals_ids = unique_vals_ids
        self.unique_vals_ids_average_key = {}
        self.pre_ids_bitmap = {}
        # self.pre_ids(unique_vals_ids)
        # self.unique_vals_map = {}
        self.ids_list = []
        self.ids_histogram_level = 1
        self.rdc_adjacency_matrix_dict = rdc_adjacency_matrix_dict
        # if rdc_adjacency_matrix_dict:
        #     if self.get_max_RDC(rdc_adjacency_matrix_dict, scope) >= 0.7:
        #         self.ids_histogram_level = 1
        #     elif self.get_max_RDC(rdc_adjacency_matrix_dict, scope) >= 0.3:
        #         self.ids_histogram_level = 2
        #     else:
        #         self.ids_histogram_level = 3
        # self.histogram_ids(unique_vals_ids, probabilities)
        # will be updated later
        self.prob_sum = None
        self.null_value_prob = None
        self.mean = None
        self.inverted_mean = None
        self.square_mean = None
        self.inverted_square_mean = None

        if not isinstance(probabilities, np.ndarray):
            probabilities = np.array(probabilities)
        self.update_from_new_probabilities(probabilities)

    def get_max_RDC(self, rdc_adjacency_matrix_dict, scope):
        scope_index = list(rdc_adjacency_matrix_dict.keys()).index(scope[0])
        return np.delete(rdc_adjacency_matrix_dict[scope[0]], scope_index).max()

    def map_unique_vals_2_list(self, unique_vals_ids):
        start = 0
        for key, value in unique_vals_ids.items():
            self.ids_list += list(value)
            num = len(value)
            self.unique_vals_map[key] = (start, num)
            start += num

    def pre_ids(self, unique_vals_ids):
        self.pre_ids_bitmap.append(RoaringBitmap())
        for i in range(len(unique_vals_ids)):
            temp = RoaringBitmap()
            c = 0
            for key, value in unique_vals_ids.items():
                if c <= i:
                    temp |= value
                    c += 1
                else:
                    break
            self.pre_ids_bitmap.append(temp)

    def histogram_ids(self, unique_vals_ids, probabilities):
        if self.ids_histogram_level == 1:
            k = 20
        elif self.ids_histogram_level == 2:
            k = 20
        elif self.ids_histogram_level == 3:
            k = 20
        bin_threshold = math.ceil(len(unique_vals_ids) / k)
        if len(unique_vals_ids.keys()) > bin_threshold:
            key_list = list(unique_vals_ids.keys())
            for i in range(bin_threshold):
                keys = []
                values = RoaringBitmap()
                key_porb = []
                bin_size = math.ceil(len(key_list) / bin_threshold)
                sum_key = 0
                for j in range(bin_size):
                    if i * bin_size + j >= len(key_list):
                        break
                    keys.append(key_list[i * bin_size + j])
                    values |= unique_vals_ids[key_list[i * bin_size + j]]
                    key_porb.append(probabilities[i * bin_size + j])
                    sum_key += key_list[i * bin_size + j] * probabilities[i * bin_size + j] * self.cardinality
                if keys:
                    self.unique_vals_ids[tuple(keys)] = (values, key_porb)
                    self.unique_vals_ids_average_key[tuple(keys)] = sum_key / len(values)
        else:
            self.unique_vals_ids = unique_vals_ids

    def copy_node(self):
        self_copy = IdentityNumericLeaf(np.copy(self.unique_vals), self.return_histogram(copy=True), self.null_value,
                                        self.scope, cardinality=self.cardinality, unique_vals_ids=self.unique_vals_ids)
        # assert self_copy.mean == self.mean and self_copy.null_value_prob == self.null_value_prob
        # assert self_copy.inverted_mean == self.inverted_mean and self_copy.square_mean == self.square_mean
        # assert self_copy.inverted_square_mean == self.inverted_square_mean
        return self_copy

    def update_unique_vals_idx(self):
        # unique_vals_idx中存储的是unique_vals中每一个值所对应的位置，字典
        self.unique_vals_idx = {self.unique_vals[idx]: idx for idx in range(self.unique_vals.shape[0])}

    def return_histogram(self, copy=True):
        if copy:
            return np.copy(self.prob_sum[1:] - self.prob_sum[:-1])
        else:
            return self.prob_sum[1:] - self.prob_sum[:-1]

    def update_from_new_probabilities(self, p):
        assert len(p) == len(self.unique_vals)
        # convert p back to cumulative prob sum
        self.prob_sum = np.concatenate([[0], np.cumsum(p)])
        # update null value prob
        not_null_indexes = np.where(self.unique_vals != self.null_value)[0]
        if self.null_value in self.unique_vals_idx.keys():
            self.null_value_prob = p[self.unique_vals_idx[self.null_value]]
        else:
            self.null_value_prob = 0
        # update not_null idxs
        zero_in_dataset = 0 in self.unique_vals_idx.keys()
        # all values NAN
        if len(not_null_indexes) == 0:
            self.mean = 0
            self.inverted_mean = np.nan

            # for variance computation
            self.square_mean = 0
            self.inverted_square_mean = np.nan
        # some values nan
        else:
            self.mean = np.dot(self.unique_vals[not_null_indexes], p[not_null_indexes]) / (1 - self.null_value_prob)
            self.square_mean = np.dot(np.square(self.unique_vals[not_null_indexes]), p[not_null_indexes]) / (
                    1 - self.null_value_prob)

            if zero_in_dataset:
                self.inverted_mean = np.nan
                self.inverted_square_mean = np.nan
            else:
                self.inverted_mean = np.dot(1 / self.unique_vals[not_null_indexes], p[not_null_indexes]) / (
                        1 - self.null_value_prob)
                self.inverted_square_mean = np.dot(1 / np.square(self.unique_vals[not_null_indexes]),
                                                   p[not_null_indexes]) / (1 - self.null_value_prob)


def _interval_probability(node, left, right, null_value, left_included, right_included):
    if left == -np.inf:
        lower_idx = 0
    else:
        lower_idx = np.searchsorted(node.unique_vals, left, side='left')
        if left == right == node.unique_vals[lower_idx - 1]:
            return node.prob_sum[lower_idx + 1] - node.prob_sum[lower_idx]

    if right == np.inf:
        higher_idx = len(node.unique_vals)
    else:
        higher_idx = np.searchsorted(node.unique_vals, right, side='right')

    if lower_idx == higher_idx:
        return 0

    p = node.prob_sum[higher_idx] - node.prob_sum[lower_idx]
    # null value included in interval
    if null_value is not None and \
            (left < null_value < right or
             null_value == left and left_included or
             null_value == right and right_included):
        p -= node.null_value_prob

    # left value should not be included in interval
    if not left_included and node.unique_vals[lower_idx] == left:
        # equivalent to p -= node.probs[lower_idx]
        p -= node.prob_sum[lower_idx + 1] - node.prob_sum[lower_idx]
    # same check for right value
    if not right_included and node.unique_vals[higher_idx - 1] == right and left != right:
        p -= node.prob_sum[higher_idx] - node.prob_sum[higher_idx - 1]
    return p


def _interval_probability_ids(node, left, right, null_value, left_included, right_included):
    if left == -np.inf:
        lower_idx = 0
    else:
        lower_idx = np.searchsorted(node.unique_vals, left, side='left')
        if left == right == node.unique_vals[lower_idx - 1]:
            return node.prob_sum[lower_idx + 1] - node.prob_sum[lower_idx], node.pre_ids_bitmap[lower_idx + 1] - node.pre_ids_bitmap[lower_idx]

    if right == np.inf:
        higher_idx = len(node.unique_vals)
    else:
        higher_idx = np.searchsorted(node.unique_vals, right, side='right')

    if lower_idx == higher_idx:
        return 0, RoaringBitmap()

    p = node.prob_sum[higher_idx] - node.prob_sum[lower_idx]
    id_bitmap = node.pre_ids_bitmap[higher_idx] - node.pre_ids_bitmap[lower_idx]
    # print(p, id_bitmap)
    # null value included in interval
    if null_value is not None and \
            (left < null_value < right or
             null_value == left and left_included or
             null_value == right and right_included):
        p -= node.null_value_prob

    # left value should not be included in interval
    if not left_included and node.unique_vals[lower_idx] == left:
        # equivalent to p -= node.probs[lower_idx]
        p -= node.prob_sum[lower_idx + 1] - node.prob_sum[lower_idx]
        id_bitmap -= node.pre_ids_bitmap[lower_idx + 1] - node.pre_ids_bitmap[lower_idx]
    # same check for right value
    if not right_included and node.unique_vals[higher_idx - 1] == right and left != right:
        p -= node.prob_sum[higher_idx] - node.prob_sum[higher_idx - 1]
        id_bitmap -= node.pre_ids_bitmap[higher_idx] - node.pre_ids_bitmap[higher_idx - 1]
    return p, id_bitmap


def _interval_expectation(power, node, left, right, null_value, left_included, right_included, inverted=False):
    lower_idx = np.searchsorted(node.unique_vals, left, side='left')
    higher_idx = np.searchsorted(node.unique_vals, right, side='right')
    exp = 0

    for j in np.arange(lower_idx, higher_idx):
        if node.unique_vals[j] == null_value:
            continue
        if node.unique_vals[j] == left and not left_included:
            continue
        if node.unique_vals[j] == right and not right_included:
            continue
        p_j = node.prob_sum[j + 1] - node.prob_sum[j]
        if power == 1:
            if not inverted:
                exp += p_j * node.unique_vals[j]
            else:
                exp += p_j * 1 / node.unique_vals[j]
        elif power == 2:
            if not inverted:
                exp += p_j * node.unique_vals[j] * node.unique_vals[j]
            else:
                exp += p_j * 1 / node.unique_vals[j] * 1 / node.unique_vals[j]

    return exp


def _interval_expectation_ids(power, node, left, right, null_value, left_included, right_included, inverted=False, ids_list=RoaringBitmap()):
    lower_idx = np.searchsorted(node.unique_vals, left, side='left')
    higher_idx = np.searchsorted(node.unique_vals, right, side='right')
    exp = 0
    count = 0
    if ids_list:
        in_list = RoaringBitmap()
        for j in np.arange(lower_idx, higher_idx):
            if node.unique_vals[j] == null_value:
                continue
            if node.unique_vals[j] == left and not left_included:
                continue
            if node.unique_vals[j] == right and not right_included:
                continue
            if node.unique_vals_ids_average_key:
                p_j = node.prob_sum[j + 1] - node.prob_sum[j]
                exp += p_j * node.unique_vals[j]
            else:
                temp_list = ids_list & node.unique_vals_ids[node.unique_vals[j]]
                exp += len(temp_list) * node.unique_vals[j]
                count += len(temp_list)
                # in_list |= temp_list

        if count:
            exp /= count
        return exp, in_list
    else:
        for j in np.arange(lower_idx, higher_idx):
            if node.unique_vals[j] == null_value:
                continue
            if node.unique_vals[j] == left and not left_included:
                continue
            if node.unique_vals[j] == right and not right_included:
                continue
            p_j = node.prob_sum[j + 1] - node.prob_sum[j]
            exp += p_j * node.unique_vals[j]
        # for key, values in node.unique_vals_ids.items():
        #     if isinstance(key, tuple) and values[0]:
        #         bitmap = values[0]
        #         key_pro = values[1]
        #         key_l, key_r = key[0], key[-1]
        #         if inclusive[0] and inclusive[1]:
        #             if interval[0] <= key_l and key_r <= interval[1]:
        #                 ids_list |= bitmap
        #             elif interval[0] <= key_l <= interval[1] or interval[0] <= key_r <= interval[1]:
        #                 for k_i in range(len(key)):
        #                     if interval[0] <= key[k_i] <= interval[1]:
        #                         count += key_pro[k_i]
        #         elif not inclusive[0] and inclusive[1]:
        #             if interval[0] < key_l and key_r <= interval[1]:
        #                 ids_list |= bitmap
        #             elif interval[0] < key_l <= interval[1] or interval[0] < key_r <= interval[1]:
        #                 for k_i in range(len(key)):
        #                     if interval[0] < key[k_i] <= interval[1]:
        #                         count += key_pro[k_i]
        #         elif inclusive[0] and not inclusive[1]:
        #             if interval[0] <= key_l and key_r < interval[1]:
        #                 ids_list |= bitmap
        #             elif interval[0] <= key_l < interval[1] or interval[0] <= key_r < interval[1]:
        #                 for k_i in range(len(key)):
        #                     if interval[0] <= key[k_i] < interval[1]:
        #                         count += key_pro[k_i]
        #         elif interval[0] < key_l and key_r < interval[1]:
        #             ids_list |= bitmap
        #         elif interval[0] < key_l < interval[1] or interval[0] < key_r < interval[1]:
        #             for k_i in range(len(key)):
        #                 if interval[0] < key[k_i] < interval[1]:
        #                     count += key_pro[k_i]
        #     elif values:
        #         if inclusive[0] and inclusive[1] and interval[0] <= key <= interval[1]:
        #             ids_list |= values
        #         elif not inclusive[0] and inclusive[1] and interval[0] < key <= interval[1]:
        #             ids_list |= values
        #         elif inclusive[0] and not inclusive[1] and interval[0] <= key < interval[1]:
        #             ids_list |= values
        #         elif interval[0] < key < interval[1]:
        #             ids_list |= values
        return exp, ids_list


def identity_expectation_ids(node, data, inverted=False, power=1, c_ids=RoaringBitmap()):
    # c_ids表示在prod节点筛选出的
    # data表示查询条件
    exps = np.zeros((data.shape[0], 1))
    exps_out = np.zeros((data.shape[0], 1))
    ranges = data[:, node.scope[0]]
    ids_list = copy.copy(c_ids)
    # start_t = perf_counter()

    # if not ids_list:
    #     return exps, RoaringBitmap(), exps_out
    if isinstance(ids_list, RoaringBitmap) and len(ids_list) == 0:
        return exps, RoaringBitmap(), exps_out
    if not isinstance(ids_list, RoaringBitmap) or len(ids_list)/node.cardinality > 10: # 为什么要用这种糖丸了的判定方式判断是不是全集？是不是没有当前prod节点上的限定条件？
        ids_list = RoaringBitmap()
    for i, rang in enumerate(ranges):
        # 对于每个条件，分别数出来有多少行，并且计算exp
        if node.null_value_prob > 0:
            assert rang is not None, "Ensure that features of expectations are not null."

        if rang is None or rang.ranges == [[-np.inf, np.inf]]:
            if ids_list:
                # 计算在指定的ids_list中，该列的数值平均值
                count = 0
                for key, values in node.unique_vals_ids.items():
                    if isinstance(key, tuple) and values[0]:
                        # 如果key是一个范围
                        bitmap = values[0]
                        # 计算外面筛选出的ids_list和该key对应的bitmap的交集数量
                        temp_count = ids_list.intersection_len(bitmap)
                        # 值与行数相乘
                        exps[i] += node.unique_vals_ids_average_key[key] * temp_count
                        count += temp_count
                    elif values:
                        # 如果key是一个具体的值
                        temp_count = ids_list.intersection_len(values)
                        # 值×行数
                        exps[i] += key * temp_count
                        count += temp_count
                if count:
                    exps[i] /= count * (1 - node.null_value_prob)
            else:
                exps[i] = node.mean * (1 - node.null_value_prob)
                # for values in node.unique_vals_ids.values():
                #     ids_list |= values
            exps_out[i] = node.mean * (1 - node.null_value_prob)
            continue
        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            temp_exp, ids_list = _interval_expectation_ids(power, node, interval[0], interval[1], rang.null_value, inclusive[0],
                                             inclusive[1], inverted=inverted, ids_list=ids_list)
            exps[i] += temp_exp
            exps_out[i] += temp_exp
    # end_t = perf_counter()
    # print(end_t - start_t)
    return exps, ids_list, exps_out


def identity_expectation(node, data, inverted=False, power=1):
    exps = np.zeros((data.shape[0], 1))
    ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):

        if node.null_value_prob > 0:
            assert rang is not None, "Ensure that features of expectations are not null."

        if rang is None or rang.ranges == [[-np.inf, np.inf]]:
            if power == 1:
                if not inverted:
                    exps[i] = node.mean * (1 - node.null_value_prob)
                else:
                    exps[i] = node.inverted_mean * (1 - node.null_value_prob)
            elif power == 2:
                if not inverted:
                    exps[i] = node.square_mean * (1 - node.null_value_prob)
                else:
                    exps[i] = node.inverted_square_mean * (1 - node.null_value_prob)
            else:
                raise NotImplementedError

            continue

        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]

            exps[i] += _interval_expectation(power, node, interval[0], interval[1], rang.null_value, inclusive[0],
                                             inclusive[1], inverted=inverted)
    return exps


def _convert_to_single_tuple_set(scope, values):
    if values is None:
        return [scope], None

    return [scope], set(map(lambda x: (x,), values))


def identity_distinct_ranges(node, data, dtype=np.float64, **kwargs):
    """
    Returns distinct values.
    """
    ranges = data[:, node.scope[0]]

    assert len(ranges) == 1, "Only single range is supported"
    if ranges[0] is None:
        return _convert_to_single_tuple_set(node.scope[0], node.unique_vals)

    assert len(ranges[0].ranges) == 1, "Only single interval is supported"

    interval = ranges[0].ranges[0]
    inclusive = ranges[0].inclusive_intervals[0]

    lower_idx = np.searchsorted(node.unique_vals, interval[0], side='left')
    higher_idx = np.searchsorted(node.unique_vals, interval[1], side='right')

    if lower_idx == higher_idx:
        return _convert_to_single_tuple_set(node.scope[0], None)

    if node.unique_vals[lower_idx] == interval[0] and not inclusive[0]:
        lower_idx += 1

    if node.unique_vals[higher_idx - 1] == interval[1] and not inclusive[1]:
        higher_idx -= 1

    if lower_idx == higher_idx:
        return _convert_to_single_tuple_set(node.scope[0], None)

    vals = set(node.unique_vals[lower_idx:higher_idx])
    if ranges[0].null_value in vals:
        vals.remove(ranges[0].null_value)

    return _convert_to_single_tuple_set(node.scope[0], vals)


def identity_likelihood_wo_null(node, data, dtype=np.float64, **kwargs):
    assert len(node.scope) == 1, node.scope

    probs = np.empty((data.shape[0], 1), dtype=dtype)
    probs[:] = np.nan
    nd = data[:, node.scope[0]]

    for i, val in enumerate(nd):
        if not np.isnan(val):
            probs[i] = _interval_probability(node, val, val, None, True, True)

    return probs


def id_process(left, right, left_included, right_included, ids_list, key, values):
    if left_included and right_included and left <= key <= right:
        ids_list |= values
    elif not left_included and right_included and left < key <= right:
        ids_list |= values
    elif left_included and not right_included and left <= key < right:
        ids_list |= values
    elif left < key < right:
        ids_list |= values
    return ids_list


def identity_likelihood_range_ids(node, data, dtype=np.float64, overwrite_ranges=None, **kwargs):
    assert len(node.scope) == 1, node.scope
    probs = np.zeros((data.shape[0], 1), dtype=dtype)
    ids_list = RoaringBitmap()
    ranges = overwrite_ranges
    intersection_p, count = 0.0, 0.0

    if overwrite_ranges is None:
        ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):
        # Skip if no range is specified aka use a log-probability of 0 for that instance
        # print(rang.is_not_null_condition, node.null_value_prob)
        if rang is None:
            probs[i] = 1
            # ids_list = node.pre_ids_bitmap[-1]
            for values in node.unique_vals_ids.values():
                ids_list |= values
            continue

        if rang.is_not_null_condition:
            # node.null_value_prob是一列中值为NULL的元组数量的比例
            probs[i] = 1 - node.null_value_prob
            if node.null_value_prob == 0:
                # ids_list = node.pre_ids_bitmap[-1]
                for values in node.unique_vals_ids.values():
                    ids_list |= values
            continue

        # Skip if no values for the range are provided
        if rang.is_impossible():
            continue

        start_t = perf_counter()
        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            probs[i] += _interval_probability(node, interval[0], interval[1], rang.null_value, inclusive[0],
                                              inclusive[1])
            # probs[i] += temp[0]
            # ids_list = temp[1]
            # start, num = -1, 0
            for key, values in node.unique_vals_ids.items():
                if isinstance(key, tuple) and values[0]:
                    bitmap = values[0]
                    key_pro = values[1]
                    key_l, key_r = key[0], key[-1]
                    if inclusive[0] and inclusive[1]:
                        if interval[0] <= key_l and key_r <= interval[1]:
                            ids_list |= bitmap
                        elif interval[0] <= key_l <= interval[1] or interval[0] <= key_r <= interval[1]:
                            for k_i in range(len(key)):
                                if interval[0] <= key[k_i] <= interval[1]:
                                    count += key_pro[k_i]
                            # for item in key:
                                # temp_count = 0
                                # if interval[0] <= item <= interval[1]:
                                #     temp_count += 1
                                # count += len(bitmap) * temp_count / len(key)
                            # ids_list |= RoaringBitmap(random.sample(list(bitmap), int(temp_count * len(bitmap) / len(key))))
                    elif not inclusive[0] and inclusive[1]:
                        if interval[0] < key_l and key_r <= interval[1]:
                            ids_list |= bitmap
                        elif interval[0] < key_l <= interval[1] or interval[0] < key_r <= interval[1]:
                            for k_i in range(len(key)):
                                if interval[0] < key[k_i] <= interval[1]:
                                    count += key_pro[k_i]
                    elif inclusive[0] and not inclusive[1]:
                        if interval[0] <= key_l and key_r < interval[1]:
                            ids_list |= bitmap
                        elif interval[0] <= key_l < interval[1] or interval[0] <= key_r < interval[1]:
                            for k_i in range(len(key)):
                                if interval[0] <= key[k_i] < interval[1]:
                                    count += key_pro[k_i]
                    elif interval[0] < key_l and key_r < interval[1]:
                        ids_list |= bitmap
                    elif interval[0] < key_l < interval[1] or interval[0] < key_r < interval[1]:
                        for k_i in range(len(key)):
                            if interval[0] < key[k_i] < interval[1]:
                                count += key_pro[k_i]
                elif values:
                    if inclusive[0] and inclusive[1] and interval[0] <= key <= interval[1]:
                        # if start < 0:
                        #     start = node.unique_vals_map[key][0]
                        # num += node.unique_vals_map[key][1]
                        ids_list |= values
                    elif not inclusive[0] and inclusive[1] and interval[0] < key <= interval[1]:
                        ids_list |= values
                    elif inclusive[0] and not inclusive[1] and interval[0] <= key < interval[1]:
                        ids_list |= values
                    elif interval[0] < key < interval[1]:
                        ids_list |= values
            # if start >= 0:
            #     ids_list |= RoaringBitmap(node.ids_list[start:start+num])

        # if ids_list:
            # intersection_p = count / len(ids_list)
        if ids_list:
            intersection_p = count
        # end_t = perf_counter()
        # print(end_t - start_t)
    if not np.all(probs == 0) and not ids_list:
        return probs, [], 0.0
    # print(probs, len(ids_list) / node.cardinality, intersection_p)
    return probs, ids_list, intersection_p


def pre_ec_identity_likelihood_range_ids(node, data, dtype=np.float64, overwrite_ranges=None, **kwargs):
    assert len(node.scope) == 1, node.scope
    probs = np.zeros((data.shape[0], 1), dtype=dtype)
    ids_list = RoaringBitmap()
    ranges = overwrite_ranges
    intersection_p, count = 0.0, 0.0

    if overwrite_ranges is None:
        ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):
        if rang is None:
            probs[i] = 1
            for key, value in node.unique_vals_ids.items():
                if len(key) == len(node.unique_vals):
                    ids_list = node.pre_ids_bitmap[key]
                    break
            continue

        if rang.is_not_null_condition:
            # node.null_value_prob是一列中值为NULL的元组数量的比例
            probs[i] = 1 - node.null_value_prob
            if node.null_value_prob == 0:
                for key, value in node.unique_vals_ids.items():
                    if len(key) == len(node.unique_vals):
                        ids_list = node.pre_ids_bitmap[key]
                        break
            continue

        # Skip if no values for the range are provided
        if rang.is_impossible():
            continue

        start_t = perf_counter()
        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            probs[i] += _interval_probability(node, interval[0], interval[1], rang.null_value, inclusive[0],
                                              inclusive[1])
            # probs[i] += temp[0]
            # ids_list = temp[1]
            start, end, tf = None, None, False
            for k, v in node.pre_ids_bitmap.items():
                key = k[-1]
                if inclusive[0] and inclusive[1] and interval[0] <= key <= interval[1]:
                    if start:
                        end = k
                    else:
                        start = k
                elif not inclusive[0] and inclusive[1] and interval[0] < key <= interval[1]:
                    if start:
                        end = k
                    else:
                        start = k
                elif inclusive[0] and not inclusive[1] and interval[0] <= key < interval[1]:
                    if start:
                        end = k
                    else:
                        start = k
                elif interval[0] < key < interval[1]:
                    if start:
                        end = k
                    else:
                        start = k
            if start and end:
                ids_list = node.pre_ids_bitmap[end][0] - node.pre_ids_bitmap[start][0]

        # end_t = perf_counter()
        # print(end_t - start_t)
    if not np.all(probs == 0) and not ids_list:
        return probs, [], 0.0
    # print(probs, len(ids_list) / node.cardinality, intersection_p)
    intersection_p = probs[0][0] - len(ids_list)/node.cardinality
    # print(intersection_p)
    return probs, ids_list, intersection_p


def pre_identity_likelihood_range_ids(node, data, dtype=np.float64, overwrite_ranges=None, **kwargs):
    assert len(node.scope) == 1, node.scope
    probs = np.zeros((data.shape[0], 1), dtype=dtype)
    ids_list = RoaringBitmap()
    ranges = overwrite_ranges
    intersection_p, count = 0.0, 0.0

    if overwrite_ranges is None:
        ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):
        if rang is None:
            probs[i] = 1
            ids_list = node.pre_ids_bitmap[-1]
            continue

        if rang.is_not_null_condition:
            # node.null_value_prob是一列中值为NULL的元组数量的比例
            probs[i] = 1 - node.null_value_prob
            if node.null_value_prob == 0:
                ids_list = node.pre_ids_bitmap[-1]
            continue

        # Skip if no values for the range are provided
        if rang.is_impossible():
            continue

        start_t = perf_counter()
        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            probs[i] += _interval_probability(node, interval[0], interval[1], rang.null_value, inclusive[0],
                                              inclusive[1])
            # probs[i] += temp[0]
            # ids_list = temp[1]
            start, num, tf = -1, 0, False
            for num_i in range(len(node.unique_vals)):
                key = node.unique_vals[num_i]
                if inclusive[0] and inclusive[1] and interval[0] <= key <= interval[1]:
                    if tf:
                        num += 1
                    else:
                        tf = True
                        start = num_i
                        num += 1
                elif not inclusive[0] and inclusive[1] and interval[0] < key <= interval[1]:
                    if tf:
                        num += 1
                    else:
                        tf = True
                        start = num_i
                        num += 1
                elif inclusive[0] and not inclusive[1] and interval[0] <= key < interval[1]:
                    if tf:
                        num += 1
                    else:
                        tf = True
                        start = num_i
                        num += 1
                elif interval[0] < key < interval[1]:
                    if tf:
                        num += 1
                    else:
                        tf = True
                        start = num_i
                        num += 1
            # print(start, num)
            if num >= 0:
                ids_list = node.pre_ids_bitmap[start + num] - node.pre_ids_bitmap[start]

        # end_t = perf_counter()
        # print(end_t - start_t)
    if not np.all(probs == 0) and not ids_list:
        return probs, [], 0.0
    # print(probs, len(ids_list) / node.cardinality, intersection_p)
    return probs, ids_list, intersection_p


def list_identity_likelihood_range_ids(node, data, dtype=np.float64, overwrite_ranges=None, **kwargs):
    assert len(node.scope) == 1, node.scope
    probs = np.zeros((data.shape[0], 1), dtype=dtype)
    ids_list = RoaringBitmap()
    ranges = overwrite_ranges
    intersection_p, count = 0.0, 0.0

    if overwrite_ranges is None:
        ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):
        if rang is None:
            probs[i] = 1
            ids_list = RoaringBitmap(node.ids_list)
            continue

        if rang.is_not_null_condition:
            # node.null_value_prob是一列中值为NULL的元组数量的比例
            probs[i] = 1 - node.null_value_prob
            if node.null_value_prob == 0:
                ids_list = RoaringBitmap(node.ids_list)
            continue

        # Skip if no values for the range are provided
        if rang.is_impossible():
            continue

        start_t = perf_counter()
        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            probs[i] += _interval_probability(node, interval[0], interval[1], rang.null_value, inclusive[0],
                                              inclusive[1])
            start, num, tf = -1, 0, False
            for m_k, m_v in node.unique_vals_map.items():
                if inclusive[0] and inclusive[1] and interval[0] <= m_k <= interval[1]:
                    if tf:
                        num += m_v[1]
                    else:
                        tf = True
                        start = m_v[0]
                        num += m_v[1]
                elif not inclusive[0] and inclusive[1] and interval[0] < m_k <= interval[1]:
                    if tf:
                        num += m_v[1]
                    else:
                        tf = True
                        start = m_v[0]
                        num += m_v[1]
                elif inclusive[0] and not inclusive[1] and interval[0] <= m_k < interval[1]:
                    if tf:
                        num += m_v[1]
                    else:
                        tf = True
                        start = m_v[0]
                        num += m_v[1]
                elif interval[0] < m_k < interval[1]:
                    if tf:
                        num += m_v[1]
                    else:
                        tf = True
                        start = m_v[0]
                        num += m_v[1]
            # end_t = perf_counter()
            # print('1:', end_t - start_t, start, start+num)
            if num > 0:
                ids_list = RoaringBitmap(node.ids_list[start:start+num])

        end_t = perf_counter()
        print(end_t - start_t)
    if not np.all(probs == 0) and not ids_list:
        return probs, [], 0.0
    # print(probs, len(ids_list) / node.cardinality, intersection_p)
    return probs, ids_list, intersection_p


def identity_likelihood_range(node, data, dtype=np.float64, overwrite_ranges=None, **kwargs):
    assert len(node.scope) == 1, node.scope
    probs = np.zeros((data.shape[0], 1), dtype=dtype)
    ranges = overwrite_ranges

    if overwrite_ranges is None:
        ranges = data[:, node.scope[0]]

    for i, rang in enumerate(ranges):
        # Skip if no range is specified aka use a log-probability of 0 for that instance
        # print(rang.is_not_null_condition, node.null_value_prob)
        if rang is None:
            probs[i] = 1
            continue

        if rang.is_not_null_condition:
            # node.null_value_prob是一列中值为NULL的元组数量的比例
            probs[i] = 1 - node.null_value_prob
            continue

        # Skip if no values for the range are provided
        if rang.is_impossible():
            continue

        for k, interval in enumerate(rang.get_ranges()):
            inclusive = rang.inclusive_intervals[k]
            probs[i] += _interval_probability(node, interval[0], interval[1], rang.null_value, inclusive[0],
                                              inclusive[1])

    return probs


def categorical_likelihood_wo_null(node, data, dtype=np.float64, **kwargs):
    """
    Returns the likelihood for the given values ignoring NULL values
    """
    probs = np.empty((data.shape[0], 1))
    probs[:] = np.nan
    for i in range(data.shape[0]):
        value = data[i, node.scope[0]]
        if not np.isnan(value):
            probs[i] = node.p[int(value)]
    # probs = np.reshape([node.p[val] for val in data[:, node.scope[0]]],
    #                    (data.shape[0], 1))

    return probs


def categorical_likelihood_range_ids(node, data, dtype=np.float64, **kwargs):
    """
    Returns the probability for the given sets.
    """
    # start_t = perf_counter()

    # Assert that the given node is only build on one instance
    assert len(node.scope) == 1, node.scope
    # print(len(node.p), node.scope)

    # Initialize the return variable log_probs with zeros
    probs = np.ones((data.shape[0], 1), dtype=dtype)
    ids_list = RoaringBitmap()
    # Only select the ranges for the specific feature
    ranges = data[:, node.scope[0]]

    # For each instance
    for i, rang in enumerate(ranges):

        # Skip if no range is specified aka use a log-probability of 0 for that instance
        if rang is None:
            continue

        if rang.is_not_null_condition:
            probs[i] = 1 - node.p[rang.null_value]
            if not rang.null_value:
                for values in node.unique_vals_ids.values():
                    ids_list |= values
            continue

        # Skip if no values for the range are provided
        if len(rang.possible_values) == 0:
            probs[i] = 0

        # Compute the sum of the probability of all possible values
        probs[i] = 0
        for possible_val in rang.possible_values:
            if node.unique_vals_ids is not None and possible_val in node.unique_vals_ids.keys():
                ids_list |= node.unique_vals_ids[possible_val]
            probs[i] += node.p[possible_val]
    return probs, ids_list, 0.0


def categorical_likelihood_range(node, data, dtype=np.float64, **kwargs):
    """
    Returns the probability for the given sets.
    """
    # Assert that the given node is only build on one instance
    assert len(node.scope) == 1, node.scope
    # print(len(node.p), node.scope)

    # Initialize the return variable log_probs with zeros
    probs = np.ones((data.shape[0], 1), dtype=dtype)
    # Only select the ranges for the specific feature
    ranges = data[:, node.scope[0]]

    # For each instance
    for i, rang in enumerate(ranges):

        # Skip if no range is specified aka use a log-probability of 0 for that instance
        if rang is None:
            continue

        if rang.is_not_null_condition:
            probs[i] = 1 - node.p[rang.null_value]
            continue

        # Skip if no values for the range are provided
        if len(rang.possible_values) == 0:
            probs[i] = 0

        # Compute the sum of the probability of all possible values
        probs[i] = 0
        for possible_val in rang.possible_values:
            probs[i] += node.p[possible_val]

    return probs

def categorical_distinct_ranges(node, data, dtype=np.float64, **kwargs):
    """
    Returns distinct values.
    """

    ranges = data[:, node.scope[0]]
    assert len(ranges) == 1, "Only single range condition is supported"

    if ranges[0] is None:
        return _convert_to_single_tuple_set(node.scope[0], np.where(node.p > 0)[0])

    return _convert_to_single_tuple_set(node.scope[0],
                                        set(np.where(node.p > 0)[0]).intersection(ranges[0].possible_values))
