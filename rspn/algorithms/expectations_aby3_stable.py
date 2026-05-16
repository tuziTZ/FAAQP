import numpy as np
import logging
from spn.structure.Base import Product, Leaf
# from tables import Leaf
# from aqp_spn.aqp_spn import DummyLeaf
from rspn.algorithms.ranges import NominalRange, NumericRange
from rspn.structure.base import Sum
from rspn.structure.leaves import IdentityNumericLeaf, Categorical


TYPE_SUM = 0
TYPE_PROD = 1
TYPE_LEAF = 2

logger = logging.getLogger(__name__)


class DummyLeaf(Leaf):
    def __init__(self):
        Leaf.__init__(self, scope=[])
        self.cardinality = 0

# ==========================================
# ABY3 算子模拟器
# ==========================================


class ABY3Simulator:
    """ABY3 基础算子模拟（密文操作）"""

    # --- 布尔域算子 ---
    @staticmethod
    def AND(a, b):
        # 强制转换为整数进行位运算
        # 假设输入是 0.0 或 1.0 的 float，或者是 int
        a_int = a.astype(np.int8) if a.dtype.kind == 'f' else a
        b_int = b.astype(np.int8) if b.dtype.kind == 'f' else b
        return np.bitwise_and(a_int, b_int)

    @staticmethod
    def OR(a, b):
        # 强制转换为 int8 以支持位运算
        _a = a.astype(np.int8) if a.dtype.kind == 'f' else a
        _b = b.astype(np.int8) if b.dtype.kind == 'f' else b
        return np.bitwise_or(_a, _b)

    @staticmethod
    def NOT(a):
        return 1 - a

    @staticmethod
    def MUX(cond, true_val, false_val):
        """
        多路复用器（密文条件分支）
        cond=1 时返回 true_val，cond=0 时返回 false_val
        公式: cond * true_val + (1-cond) * false_val
        """
        return cond * true_val + (1 - cond) * false_val

    # --- 算术域算子 ---
    @staticmethod
    def ADD(a, b):
        return a + b

    @staticmethod
    def SUB(a, b):
        return a - b

    @staticmethod
    def MUL(a, b):
        return a * b

    @staticmethod
    def DIV(a, b, epsilon=1e-9):
        return a / (b + epsilon)

    @staticmethod
    def SUM(vec):
        return np.sum(vec)

    @staticmethod
    def DOT(vec1, vec2):
        """向量点积"""
        return np.sum(vec1 * vec2)

    # --- 域转换 ---
    @staticmethod
    def B2A(bool_val):
        """布尔域转算术域"""
        return bool_val.astype(np.float64)

    @staticmethod
    def A2B(arith_val, threshold=0.5):
        """算术域转布尔域"""
        return (arith_val > threshold).astype(np.int8)

    # --- 比较算子 ---
    @staticmethod
    def GE(a, b):
        """大于等于"""
        return (a >= b).astype(np.int8)

    @staticmethod
    def LE(a, b):
        """小于等于"""
        return (a <= b).astype(np.int8)

    @staticmethod
    def EQ(a, b):
        """等于"""
        return (a == b).astype(np.int8)

    # --- 辅助函数 ---
    @staticmethod
    def create_ones(size):
        """创建全1向量"""
        return np.ones(size, dtype=np.int8)

    @staticmethod
    def create_zeros(size):
        """创建全0向量"""
        return np.zeros(size, dtype=np.int8)

    @staticmethod
    def count_ones(bit_vec):
        """统计1的个数"""
        return np.sum(bit_vec)


aby3 = ABY3Simulator()


def scalar(x):
    """标量 → 密文（算术域）"""
    return np.array([x], dtype=np.float64)


def encrypt_vector(vec):
    """列表/ndarray → 密文向量"""
    return np.array(vec, dtype=np.float64)


def encrypt_bitmap(bitmap, total_rows):
    bit_vec = np.zeros(total_rows, dtype=np.int8)
    idxs = np.fromiter(bitmap, dtype=np.int64)
    bit_vec[idxs] = 1
    return bit_vec


def encrypt_scope_bitmap(scope_indices, total_columns):
    """
    专门用于将 scope (列号集合) 转换为 Bitmap
    长度 = 总列数
    """
    bit_vec = np.zeros(total_columns, dtype=np.int8)
    if scope_indices is not None and len(scope_indices) > 0:
        # 确保转为整数索引
        idxs = np.array(list(scope_indices), dtype=np.int64)
        # 过滤掉越界的索引（防御性编程）
        idxs = idxs[idxs < total_columns]
        bit_vec[idxs] = 1
    return bit_vec


def parse_evidence_to_mask(evidence):
    """
    解析 evidence 数组，生成一个掩码向量。
    1 表示该列有查询条件 (Range对象)，0 表示该列为 None。
    """
    if evidence is None:
        return np.array([], dtype=np.int8)

    # evidence 通常是 (1, num_columns) 的形状，将其展平
    ev_flat = np.array(evidence).flatten()

    # 只要不为 None，就标记为 1
    mask = np.array(
        [1 if e is not None else 0 for e in ev_flat], dtype=np.int8)
    return mask


def parse_evidence_to_aby3_format(evidence, num_columns):
    """
    将混合类型的 evidence 转换为统一的 ABY3 兼容数值格式。
    策略：
    1. NumericRange: 直接提取 ranges 和 inclusive。
    2. NominalRange: 将 possible_values 转换为 [val, val] 的闭区间。
    """
    evidence_map = {}

    if evidence is None:
        return evidence_map

    # 展平 evidence 方便遍历 (假设输入是 (1, num_cols) 或类似形状)
    ev_flat = np.array(evidence).flatten()

    # 确保我们只处理有效列数
    limit = min(len(ev_flat), num_columns)

    for col_idx in range(limit):
        ev_obj = ev_flat[col_idx]

        if ev_obj is None:
            continue

        # 统一的数据容器
        ranges_list = []
        inclusive_list = []

        # --- 情况 A: NumericRange (数值范围) ---
        if hasattr(ev_obj, 'get_ranges') and hasattr(ev_obj, 'inclusive_intervals'):
            raw_ranges = ev_obj.get_ranges()      # e.g., [[22.0, 888.0]]
            raw_inc = ev_obj.inclusive_intervals  # e.g., [[True, True]]

            ranges_list = raw_ranges
            # 将 True/False 转换为 1/0
            inclusive_list = [[1 if b else 0 for b in pair]
                              for pair in raw_inc]

        # --- 情况 B: NominalRange (离散类别) ---
        elif hasattr(ev_obj, 'possible_values'):
            vals = ev_obj.possible_values  # e.g., array([168])

            # 将每个离散值 v 转换为闭区间 [v, v]
            for v in vals:
                ranges_list.append([float(v), float(v)])
                inclusive_list.append([1, 1])  # 离散值匹配必须是闭区间 (True, True)

        # 如果解析出了有效条件，转为 Numpy 数组
        if ranges_list:
            evidence_map[col_idx] = {
                # Shape: (N, 2)
                'ranges': np.array(ranges_list, dtype=np.float64),
                # Shape: (N, 2)
                'inclusive': np.array(inclusive_list, dtype=np.int8)
            }

    return evidence_map


def convert_aby3(spn):

    total_rows = int(spn.cardinality)

    # ===============================
    # 1. 命中 SPN cache

    logger.info("[ABY3] Converting SPN to ABY3 format...")

    def convert_node(node):
        if isinstance(node, Sum):
            node_type = TYPE_SUM
        elif isinstance(node, Product):
            node_type = TYPE_PROD
        elif isinstance(node, (IdentityNumericLeaf, Categorical, DummyLeaf)):
            node_type = TYPE_LEAF
        else:
            raise TypeError(f"Unknown node type: {type(node)}")

        aby3_node = {
            "type": node_type,
            "id": scalar(node.id),
            "scope": encrypt_vector(node.scope),
            "cardinality": scalar(node.cardinality),
            "weights": None,
            "children": [],
            "prob_sum": scalar(0.0),
            "null_value": scalar(0.0),
            "null_value_prob": scalar(0.0),
            "unique_vals_ids": {},
            "unique_vals_ids_average_key": {},
            "leaf_type": None
        }

        if hasattr(node, "children"):
            aby3_node["children"] = [convert_node(c) for c in node.children]

        if node_type == TYPE_SUM:
            aby3_node["weights"] = encrypt_vector(node.weights)
        else:
            aby3_node["weights"] = encrypt_vector([])

        if node_type == TYPE_LEAF and isinstance(node, IdentityNumericLeaf):
            aby3_node["leaf_type"] = "IdentityNumericLeaf"
            aby3_node["prob_sum"] = scalar(node.prob_sum)
            aby3_node["null_value"] = scalar(node.null_value)
            aby3_node["null_value_prob"] = scalar(node.null_value_prob)

            # 有的val是具体数值，有的是区间tuple
            for val, bitmap in node.unique_vals_ids.items():
                aby3_node["unique_vals_ids"][val] = encrypt_bitmap(
                    bitmap, total_rows
                )

            # 每个range都有一个代表数值
            for key, value in node.unique_vals_ids_average_key.items():
                aby3_node["unique_vals_ids_average_key"][key] = scalar(value)
        elif node_type == TYPE_LEAF and isinstance(node, Categorical):
            aby3_node["leaf_type"] = "Categorical"
            # 此处val表示一个类别
            for val, bitmap in node.unique_vals_ids.items():
                aby3_node["unique_vals_ids"][val] = encrypt_bitmap(
                    bitmap, total_rows
                )
        elif node_type == TYPE_LEAF and isinstance(node, DummyLeaf):
            aby3_node["leaf_type"] = "DummyLeaf"

        return aby3_node

    aby3_spn = convert_node(spn)

    return aby3_spn


# ================  V1 ==================
def expectation_recursive_aby3(node,
                               feature_scope,
                               inverted_features,
                               relevant_scope,
                               evidence,
                               node_expectation,
                               node_likelihoods,
                               c_ids_vec=None,
                               spn=False,
                               total_rows=None):
    """
    ABY3 版本 expectation_recursive
    将 c_ids (RoaringBitmap) 替换为 c_ids_vec (二进制向量),
    并使用 aby3 算子进行计算。
    """

    cardinality = node["cardinality"][0]
    if node['id'] == 0:
        total_rows = int(cardinality)
        c_ids_vec=aby3.create_ones(total_rows)

    product = scalar(1.0)

    if node["type"] == TYPE_PROD:

        exp_child_list = []
        o_child_list = []
        # 这里node["children"]也要改吧，可以直接按照id取下标吗
        for i, child in enumerate(node["children"]):
            child_scope = child["scope"].astype(int).tolist()
            child_scope_set = set(child_scope)
            # 如果child节点和relevant_scope有交集
            if len(relevant_scope.intersection(child_scope_set)) > 0:
                # 仅对有一个scope的叶子结点进行期望计算
                if child_scope[0] in feature_scope and child["type"] != TYPE_PROD and child["type"] != TYPE_SUM:
                    exp_child_list.append(child)
                else:
                    o_child_list.append(child)
        final_flag=0
        for child in o_child_list:
            # 判断节点类型使用flag
            factor, ids_list_vec, flag = expectation_recursive_aby3(
                child, feature_scope, inverted_features, relevant_scope,
                evidence, node_expectation, node_likelihoods,
                c_ids_vec=None,
                spn=spn, total_rows=total_rows
            )

            final_flag |= flag
            # 叶子结点选择率，求交集
            if flag:
                c_ids_vec = aby3.AND(c_ids_vec, ids_list_vec)
            # sum节点，直接相乘
            else:
                product = aby3.MUL(product, factor)

        # 使用最终交集计算选择率
        if final_flag:
            current_c_count = aby3.SUM(c_ids_vec)
            ratio = aby3.DIV(scalar(current_c_count), cardinality)
            product = aby3.MUL(product, ratio)


        for child in exp_child_list:
            factor, ids_list_vec, factor_out = expectation_recursive_aby3(
                child, feature_scope, inverted_features, relevant_scope,
                evidence, node_expectation, node_likelihoods,
                c_ids_vec=c_ids_vec,
                spn=spn, total_rows=total_rows
            )
            # 期望节点，直接相乘
            product = aby3.MUL(product, factor)

        final_result = product

        return final_result, None, 0
    
    elif node["type"] == TYPE_SUM:

        weights = node["weights"]
        children_results = []

        for child in node["children"]:

            res, _, _ = expectation_recursive_aby3(
                child, feature_scope, inverted_features, relevant_scope,
                evidence, node_expectation, node_likelihoods,
                c_ids_vec=aby3.create_ones(total_rows), spn=spn, total_rows=total_rows
            )
            children_results.append(res)
        # 分别乘上权重然后相加
        vals_vec = np.array([r[0] for r in children_results])

        weighted_sum = aby3.DOT(weights, vals_vec)
        normalizer = aby3.SUM(weights)
        final_val = aby3.DIV(scalar(weighted_sum), scalar(normalizer))
        return final_val, None, 0

    elif node["type"] == TYPE_LEAF:
        # if node["id"] == 901:
        #     print("debug")
        
        if node["leaf_type"] == "DummyLeaf":
            # DummyLeaf 直接返回全1位图
            return scalar(1), None, 0
    
        # 获取到node所代表的scope的列
        col_idx = int(node["scope"][0])
        # 在此列上的要求取值or限定条件
        ev_val = evidence[0, col_idx] if evidence is not None else None
        local_ids_vec = aby3.create_ones(total_rows)

        if ev_val is not None:
            local_ids_vec = aby3.create_zeros(total_rows)
            # 有限制条件：遍历叶子节点存储的所有唯一值/区间
            # unique_vals_ids 结构: { 值: bitmap位图向量 }
            if node["leaf_type"] == "IdentityNumericLeaf":
                for val_key, bitmap_vec in node["unique_vals_ids"].items():
                    is_match = False

                    # 获取查询区间及其闭合属性
                    ranges = ev_val.get_ranges()
                    inclusive = ev_val.inclusive_intervals

                    for k, interval in enumerate(ranges):
                        inc_l, inc_r = inclusive[k]

                        if isinstance(val_key, tuple):
                            # --- Tuple Key (Bucket/直方图区间) ---
                            # 逻辑参照: identity_likelihood_range_ids
                            # 只有当 Bucket 完全包含在查询区间内时，才取并集 (Strict Containment)
                            key_l, key_r = val_key[0], val_key[-1]

                            # 检查左边界
                            if inc_l:
                                lower_ok = (interval[0] <= key_l)
                            else:
                                lower_ok = (interval[0] < key_l)

                            # 检查右边界
                            if inc_r:
                                upper_ok = (key_r <= interval[1])
                            else:
                                upper_ok = (key_r < interval[1])

                            if lower_ok and upper_ok:
                                is_match = True
                                break
                        else:
                            # --- Scalar Key (单个数值) ---
                            # 逻辑参照: identity_likelihood_range_ids
                            # 检查数值是否落在查询区间内
                            v_val = val_key

                            # 检查左边界
                            if inc_l:
                                lower_ok = (interval[0] <= v_val)
                            else:
                                lower_ok = (interval[0] < v_val)

                            # 检查右边界
                            if inc_r:
                                upper_ok = (v_val <= interval[1])
                            else:
                                upper_ok = (v_val < interval[1])

                            if lower_ok and upper_ok:
                                is_match = True
                                break

                    if is_match:
                        local_ids_vec = aby3.OR(local_ids_vec, bitmap_vec)
            elif node["leaf_type"] == "Categorical":
                # if node["id"]==476:
                #     print(1) 此处修改，如果先循环possible_values，判断是否在节点的字典里，会快一些
                for val_key, bitmap_vec in node["unique_vals_ids"].items():
                    is_match = False
                    # B. 类别型 Set 对象 (Categorical)
                    # val_key 直接在 possible_values 集合中

                    if int(val_key) in ev_val.possible_values:
                        is_match = True

                    if is_match:
                        # 与符合限定条件的位图们取并集，因为可能会有很多个key符合条件
                        local_ids_vec = aby3.OR(local_ids_vec, bitmap_vec)


        # 使用上下文的筛选条件，是为了计算期望
        if c_ids_vec is not None:
            # 取交集：既满足之前的条件(c_ids)，又满足当前列条件(local)
            final_c_ids = aby3.AND(c_ids_vec, local_ids_vec)
        else:
            final_c_ids = local_ids_vec


        # 计算当前符合条件的行数 (cnt)
        cnt = aby3.SUM(local_ids_vec)

        # 如果叶子结点所代表的列已经是目标特征，这种时候需要用到外面传过来的 c_ids_vec
        is_target_feature = (col_idx in feature_scope)

        if is_target_feature:
            # === 计算条件期望 (Expectation) ===
            # E = Sum( Value * Count(Intersection（符合条件的行，取这个value的行）) ) / 符合条件的行数

            numerator = scalar(0.0)

            # 遍历所有可能的值，计算加权和
            for val_key, bitmap_vec in node["unique_vals_ids"].items():

                # 1. 取值：如果是区间元组，取写好的值
                # 原计算方式：self.unique_vals_ids_average_key[tuple(keys)] = sum_key / len(values)
                if isinstance(val_key, tuple):
                    val_num = node["unique_vals_ids_average_key"][val_key]
                else:
                    val_num = float(val_key)

                # 2. 计算该值在 final_c_ids 中出现的次数
                #    即：Final_Rows 且 Value=v 的行数
                overlap_vec = aby3.AND(final_c_ids, bitmap_vec)
                overlap_cnt = aby3.SUM(overlap_vec)

                # 3. 累加分子: val * count
                term = aby3.MUL(scalar(val_num), scalar(overlap_cnt))
                numerator = aby3.ADD(numerator, term)

            # 4. 计算期望: 分子 / 分母 (分母为 final_c_ids 的总 1 个数)
            # 后续可以想办法把这个除法累计成一个整体除法，减少除法次数
            if aby3.SUM(final_c_ids)==total_rows:
                # 全部行都符合条件，直接返回均值
                result_val = aby3.DIV(numerator, scalar(cardinality))
            else:
                result_val = aby3.DIV(numerator, scalar(aby3.SUM(final_c_ids)))
            # 返回还没和选择率相乘的期望
            return result_val, final_c_ids, 1

        else:
            # 计算选择率
            return aby3.DIV(scalar(cnt), cardinality), local_ids_vec, 1

    else:
        raise Exception('Node type unknown: ' + str(node["type"]))
