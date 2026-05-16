import copy
import logging
from time import perf_counter

import numpy as np
from spn.algorithms.Inference import likelihood
from spn.structure.Base import Product

from rspn.algorithms.expectations_aby3 import convert_aby3, expectation_recursive_aby3
from rspn.code_generation.convert_conditions import convert_range
from rspn.structure.base import Sum
from rspn.structure.leaves import identity_expectation_ids, identity_likelihood_range_ids, categorical_likelihood_range_ids, pre_identity_likelihood_range_ids, list_identity_likelihood_range_ids, pre_ec_identity_likelihood_range_ids
from roaringbitmap import RoaringBitmap
from rspn.structure.leaves import Categorical, IdentityNumericLeaf
from utils.toolkit import leaf_calculation
logger = logging.getLogger(__name__)
spn_aby3=None

# def expectation(spn, feature_scope, inverted_features, ranges, node_expectation=None, node_likelihoods=None,
#                 use_generated_code=False, spn_id=None, meta_types=None, gen_code_stats=None):
#     """Compute the Expectation:
#         E[1_{conditions} * X_feature_scope]
#         First factor is one if condition is fulfilled. For the second factor the variables in feature scope are
#         multiplied. If inverted_features[i] is True, variable is taken to denominator.
#         The conditional expectation would be E[1_{conditions} * X_feature_scope]/P(conditions)
#     """

#     # evidence_scope = set([i for i, r in enumerate(ranges) if not np.isnan(r)])
#     evidence_scope = set([i for i, r in enumerate(ranges[0]) if r is not None])
#     evidence = ranges
#     assert not (len(evidence_scope) > 0 and evidence is None)

#     relevant_scope = set()
#     relevant_scope.update(evidence_scope)
#     relevant_scope.update(feature_scope)
#     if len(relevant_scope) == 0:
#         return np.ones((ranges.shape[0], 1))

#     if ranges.shape[0] == 1:

#         applicable = True
#         if use_generated_code:
#             boolean_relevant_scope = [i in relevant_scope for i in range(len(meta_types))]
#             boolean_feature_scope = [i in feature_scope for i in range(len(meta_types))]
#             applicable, parameters = convert_range(boolean_relevant_scope, boolean_feature_scope, meta_types, ranges[0],
#                                                    inverted_features)

#         # generated C++ code
#         if use_generated_code and applicable:
#             time_start = perf_counter()
#             import optimized_inference

#             spn_func = getattr(optimized_inference, f'spn{spn_id}')
#             result = np.array([[spn_func(*parameters)]])

#             time_end = perf_counter()

#             if gen_code_stats is not None:
#                 gen_code_stats.calls += 1
#                 gen_code_stats.total_time += (time_end - time_start)

#             return result

#         else:
#             temp = np.array(
#                 [[expectation_recursive(spn, feature_scope, inverted_features, relevant_scope, evidence,
#                                         node_expectation, node_likelihoods)[0]]])
#             return temp

#     return expectation_recursive_batch(spn, feature_scope, inverted_features, relevant_scope, evidence,
#                                        node_expectation, node_likelihoods)

def expectation(spn, feature_scope, inverted_features, ranges, node_expectation=None, node_likelihoods=None,
                use_generated_code=False, spn_id=None, meta_types=None, gen_code_stats=None):
    """Compute the Expectation:
        E[1_{conditions} * X_feature_scope]
        First factor is one if condition is fulfilled. For the second factor the variables in feature scope are
        multiplied. If inverted_features[i] is True, variable is taken to denominator.
        The conditional expectation would be E[1_{conditions} * X_feature_scope]/P(conditions)
    """

    # evidence_scope = set([i for i, r in enumerate(ranges) if not np.isnan(r)])
    evidence_scope = set([i for i, r in enumerate(ranges[0]) if r is not None])
    evidence = ranges
    assert not (len(evidence_scope) > 0 and evidence is None)

    relevant_scope = set()
    relevant_scope.update(evidence_scope)
    relevant_scope.update(feature_scope)
    logger.info(
        "[QUERY TRACE][expectation] feature_scope=%s inverted_features=%s evidence_scope=%s relevant_scope=%s ranges_shape=%s",
        feature_scope,
        inverted_features,
        sorted(list(evidence_scope)),
        sorted(list(relevant_scope)),
        ranges.shape,
    )
    logger.debug(
        "[QUERY TRACE][expectation] first_row_evidence=%s",
        [str(val) if val is not None else None for val in ranges[0]],
    )
    if len(relevant_scope) == 0:
        return np.ones((ranges.shape[0], 1))

    if ranges.shape[0] == 1:

        applicable = True
        if use_generated_code:
            boolean_relevant_scope = [i in relevant_scope for i in range(len(meta_types))]
            boolean_feature_scope = [i in feature_scope for i in range(len(meta_types))]
            applicable, parameters = convert_range(boolean_relevant_scope, boolean_feature_scope, meta_types, ranges[0],
                                                   inverted_features)
        # print(evidence)
        # 把树变成aby3的存储形式
        # global spn_aby3
        # if spn_aby3==None:
        #     spn_aby3=convert_aby3(spn)
        # temp = np.array(
        #     [[expectation_recursive_aby3(spn_aby3, feature_scope, inverted_features, relevant_scope, evidence,
        #                             node_expectation, node_likelihoods)[0]]])
        temp = np.array(
            [[expectation_recursive(spn, feature_scope, inverted_features, relevant_scope, evidence,
                                    node_expectation, node_likelihoods)[0]]])
        print("expectation result:", temp[0][0])
        # temp是一个单纯的值array([[1.e-06]])
        return temp

    return expectation_recursive_batch(spn, feature_scope, inverted_features, relevant_scope, evidence,
                                       node_expectation, node_likelihoods)



def expectation_recursive_batch(node, feature_scope, inverted_features, relevant_scope, evidence, node_expectation,
                                node_likelihoods):
    if isinstance(node, Product):
        llchildren = np.concatenate(
            [expectation_recursive_batch(child, feature_scope, inverted_features, relevant_scope, evidence,
                                         node_expectation, node_likelihoods)
             for child in node.children if
             len(relevant_scope.intersection(child.scope)) > 0], axis=1)
        return np.nanprod(llchildren, axis=1).reshape(-1, 1)

    elif isinstance(node, Sum):
        if len(relevant_scope.intersection(node.scope)) == 0:
            return np.full((evidence.shape[0], 1), np.nan)
        llchildren = np.concatenate(
            [expectation_recursive_batch(child, feature_scope, inverted_features, relevant_scope, evidence,
                                         node_expectation, node_likelihoods)
             for child in node.children], axis=1)

        relevant_children_idx = np.where(np.isnan(llchildren[0]) == False)[0]
        if len(relevant_children_idx) == 0:
            return np.array([np.nan])

        weights_normalizer = sum(node.weights[j] for j in relevant_children_idx)
        b = np.array(node.weights)[relevant_children_idx] / weights_normalizer

        return np.dot(llchildren[:, relevant_children_idx], b).reshape(-1, 1)

    else:
        if node.scope[0] in feature_scope:
            t_node = type(node)
            if t_node in node_expectation:
                exps = np.zeros((evidence.shape[0], 1))

                feature_idx = feature_scope.index(node.scope[0])
                inverted = inverted_features[feature_idx]

                exps[:] = node_expectation[t_node](node, evidence, inverted=inverted)
                return exps
            else:
                raise Exception('Node type unknown: ' + str(t_node))
        return likelihood(node, evidence, node_likelihood=node_likelihoods)


def nanproduct(product, factor):
    if np.isnan(product):
        if not np.isnan(factor):
            return factor
        else:
            return np.nan
    else:
        if np.isnan(factor):
            return product
        else:
            return product * factor


def idsproduct(c_ids, ids_list):
    if not isinstance(c_ids, RoaringBitmap):
        if isinstance(ids_list, RoaringBitmap):
            return ids_list
        else:
            return None
    else:
        if not isinstance(ids_list, RoaringBitmap):
            return c_ids
        else:
            return ids_list & c_ids

# estimate results by using bitmaps
def expectation_recursive(node, feature_scope, inverted_features, relevant_scope, evidence, node_expectation,
                          node_likelihoods, c_ids=None, spn=False):
    # 对于prod节点
    if isinstance(node, Product):
        # if node.id==300:
        #     print("======")
        if len(node.scope)==0:
            return 0, None, False
        temp_range = set(list(evidence[:, node.scope][0]))
        if None in temp_range:
            temp_range.remove(None)
        if len(temp_range) <= 1 and not feature_scope:
            spn = True
        product = np.nan
        in_product, out_product = np.nan, np.nan
        product_c = 1 #初始选择率
        c_ids = [None]
        is_leaf, is_exp, is_out, is_large = False, False, False, False
        exp_child_list, o_child_list = [], []
        # 分割子节点，relevant_scope所有涉及的scope，evidence表示条件，feature_scope表示期望涉及的scope
        for child in node.children:
            if len(relevant_scope.intersection(child.scope)) > 0 and child.scope[0] in feature_scope \
                    and type(child) in node_expectation and not isinstance(child, Product) and not isinstance(child, Sum):
                        # 计算期望，仅对符合条件的叶子节点
                exp_child_list.append(child)
            elif len(relevant_scope.intersection(child.scope)) > 0:
                # 只要是sum，都当这个处理
                o_child_list.append(child)
        # 处理非期望子节点
        # if node.id==300:
        #     print("======")
        for child in o_child_list:
            factor, ids_list, temp_intersection_p = expectation_recursive(child, feature_scope, inverted_features, relevant_scope,
                                                               evidence,
                                                               node_expectation, node_likelihoods, spn=spn)
            # if temp_intersection_p:
            #     print("prod",node.id,"child:", child.id,"temp_intersection_p =", temp_intersection_p)
            if is_large:
                product = nanproduct(product, factor)
                continue
            # sum
            if not isinstance(ids_list, RoaringBitmap):
                product = nanproduct(product, factor)
                if isinstance(temp_intersection_p, float):
                    is_large = True
                    if isinstance(c_ids, RoaringBitmap):
                        product = nanproduct(product, len(c_ids) / node.cardinality + out_product)
            # 如果当前c_id还是空的，就把子节点返回的交集赋值给它，并且初始化in_product
            elif not isinstance(c_ids, RoaringBitmap):
                in_product = 0.0
                is_leaf = True
                c_ids = ids_list
            # 取最小的交集，is leaf表示当前节点是叶子节点
            # 乘积是
            elif len(c_ids) != node.cardinality and len(ids_list) == node.cardinality:
                in_product = len(c_ids) / node.cardinality
                is_leaf = True
                c_ids = c_ids
                
            elif len(c_ids) == node.cardinality and len(ids_list) != node.cardinality:
                in_product = len(c_ids) / node.cardinality
                is_leaf = True
                c_ids = ids_list
            else:
                in_product = len(c_ids) / node.cardinality
                is_leaf = True
                c_ids = idsproduct(c_ids, ids_list)
            # 错怪你了
            if isinstance(temp_intersection_p, float):
                if np.isnan(out_product):
                    out_product = temp_intersection_p
                else:
                    is_out = True
                    out_product = nanproduct(in_product, temp_intersection_p) + nanproduct(len(ids_list) / node.cardinality + temp_intersection_p, out_product)
            

        if isinstance(c_ids, RoaringBitmap) and c_ids:
            product_c = len(c_ids) / node.cardinality
        i_num = 0
        # out_product:在精确的 ID 集合（Bitmap）交集之外，满足查询条件的概率（或比例）乘积部分。
        # 计算期望子节点
        for child in exp_child_list:
            if isinstance(c_ids, RoaringBitmap) and c_ids:
                # 针对叶子节点，有期望相关的值
                # factor是一个数组，把每个条件的exp分开来返回
                factor, ids_list, factor_out = expectation_recursive(child, feature_scope, inverted_features, relevant_scope,
                                                               evidence,
                                                               node_expectation, node_likelihoods, c_ids=c_ids, spn=spn)
                if out_product > 0:
                    # 分子：
                    factor = (factor * len(c_ids) + factor_out * out_product * node.cardinality) / (len(c_ids) + out_product * node.cardinality)
                is_leaf = True
                is_exp = True
                c_ids = idsproduct(c_ids, ids_list)
                if len(ids_list) == 0:# 没有符合条件的行
                    product = 0
                    continue
                elif np.isnan(product):
                    i_num += 1
                    product = factor
                else:
                    i_num += 1
                    product *= factor

                if product_c < 1:
                    product_c = len(ids_list) / node.cardinality
            elif isinstance(c_ids, RoaringBitmap):
                if np.isnan(out_product):
                    return 0, [None], False
                elif out_product <= 0:
                    return 0, [None], False
                else:
                    factor, _, _ = expectation_recursive(child, feature_scope, inverted_features,
                                                                         relevant_scope,
                                                                         evidence,
                                                                         node_expectation, 
                                                                         node_likelihoods)
                    product = nanproduct(product, factor)
            else:
                factor, _, _ = expectation_recursive(child, feature_scope, inverted_features,
                                                                     relevant_scope,
                                                                     evidence,
                                                                     node_expectation, 
                                                                     node_likelihoods,spn=True)
                # 获取到sum节点的输出值，直接乘上即可
                product = nanproduct(product, factor)

        # c_ids表示符合查询条件的记录ID集合
        
        if isinstance(c_ids, RoaringBitmap) and not np.isnan(product) and is_exp:
            # product是sum的结果×选择率×期望
            product *= len(c_ids) / node.cardinality
        elif isinstance(c_ids, RoaringBitmap) and is_leaf and not is_large:
            # 最终选择的交集和节点的总记录数的比例，也就是选择率
            temp_product = len(c_ids) / node.cardinality
            if not np.isnan(out_product) and is_out and temp_product:
                temp_product += out_product
            if np.isnan(product):# 这条表示只有选择率，没有期望的计算
                product = temp_product
            else:# 这个表示有期望，于是是期望乘以选择率
                product *= temp_product
        # print("product node:", node.id, "result:", product)
        return product, [None], False

    elif isinstance(node, Sum):
        if len(node.scope)==0:
            return 1, None, False
        if len(relevant_scope.intersection(node.scope)) == 0:
            return np.nan, [None], False

        llchildren = [expectation_recursive(child, feature_scope, inverted_features, relevant_scope, evidence,
                                            node_expectation, node_likelihoods)[0]
                      for child in node.children]

        relevant_children_idx = np.where(np.isnan(llchildren) == False)[0]

        if len(relevant_children_idx) == 0:
            return np.nan, [None], False

        weights_normalizer = sum(node.weights[j] for j in relevant_children_idx)
        weighted_sum = sum(node.weights[j] * llchildren[j] for j in relevant_children_idx)
        return weighted_sum / weights_normalizer, [None], False

    else:
        if len(node.scope)==0:
            return 1, None, False
        # 叶子结点
        
        # if spn:
        #     if node.scope[0] in feature_scope:
        #         t_node = type(node)
        #         if t_node in node_expectation:
        #             feature_idx = feature_scope.index(node.scope[0])
        #             inverted = inverted_features[feature_idx]
        #             return node_expectation[t_node](node, evidence, inverted=inverted).item(), [None], False
        #         else:
        #             raise Exception('Node type unknown: ' + str(t_node))
        #     temp = node_likelihoods[type(node)](node, evidence)
        #     return temp.item(), [None], False
        # else:
        # 期望计算，只有数值型节点会有这种情况
        if node.scope[0] in feature_scope:
            t_node = type(node)
            if t_node in node_expectation:
                feature_idx = feature_scope.index(node.scope[0])
                inverted = inverted_features[feature_idx]
                temp = identity_expectation_ids(node, evidence, inverted=inverted, c_ids=c_ids)
                # print("exp leaf:",node.id,"result",temp[0].item())
                return temp[0].item(), temp[1], temp[2].item()
            else:
                raise Exception('Node type unknown: ' + str(t_node))
        # 选择率计算，数值型和类别型不同
        if isinstance(node, IdentityNumericLeaf):
            # 一种带有pre_id的优化情况
            # if node.pre_ids_bitmap:
            #     temp = pre_ec_identity_likelihood_range_ids(node, evidence)
            # else:
            temp = identity_likelihood_range_ids(node, evidence)
            # interception是count
        elif isinstance(node, Categorical):
            temp = categorical_likelihood_range_ids(node, evidence)
        # if temp[0]!=0:
            # print("leaf node:",node.id,"scope:",node.scope[0])
            # print(temp[0].item(),  len(temp[1]))
            # interception是0
        # print("o leaf:",node.id,"result",temp[0].item())
        return temp[0].item(), temp[1], temp[2]

