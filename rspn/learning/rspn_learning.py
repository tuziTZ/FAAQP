import logging

import numpy as np
from sklearn.cluster import KMeans
from spn.algorithms.splitting.Base import preproc, split_data_by_clusters
from spn.algorithms.splitting.RDC import getIndependentRDCGroups_py, rdc_test
from spn.structure.StatisticalTypes import MetaType
from roaringbitmap import RoaringBitmap

from rspn.structure.leaves import IdentityNumericLeaf, Categorical

logger = logging.getLogger(__name__)
MAX_UNIQUE_LEAF_VALUES = 10000


def learn_mspn(
        data,
        ds_context,
        cols="rdc",
        rows="kmeans",
        min_instances_slice=200,
        threshold=0.3,
        max_sampling_threshold_cols=10000,
        max_sampling_threshold_rows=100000,
        ohe=False,
        leaves=None,
        memory=None,
        rand_gen=None,
        cpus=-1
):
    """
    Adapts normal learn_mspn to use custom identity leafs and use sampling for structure learning.
    :param max_sampling_threshold_rows:
    :param max_sampling_threshold_cols:
    :param data:
    :param ds_context:
    :param cols:
    :param rows:
    :param min_instances_slice:
    :param threshold:
    :param ohe:
    :param leaves:
    :param memory:
    :param rand_gen:
    :param cpus:
    :return:
    """
    if leaves is None:
        leaves = create_custom_leaf

    if rand_gen is None:
        rand_gen = np.random.RandomState(17)

    from rspn.learning.structure_learning import get_next_operation, learn_structure

    def l_mspn(data, ds_context, cols, rows, min_instances_slice, threshold, ohe):
        split_cols, split_rows = get_splitting_functions(max_sampling_threshold_rows, max_sampling_threshold_cols, cols,
                                                         rows, ohe, threshold, rand_gen, cpus)
        nextop = get_next_operation(min_instances_slice)
        node = learn_structure(data, ds_context, split_rows, split_cols, leaves, next_operation=nextop)
        return node

    if memory:
        l_mspn = memory.cache(l_mspn)

    spn = l_mspn(data, ds_context, cols, rows, min_instances_slice, threshold, ohe)
    return spn


def get_RDC_value(local_data, ds_context, scope, max_sampling_threshold_cols=10000, threshold=0.3, ohe=True, k=10, s=1 / 6,
                          non_linearity=np.sin, n_jobs=-2, rand_gen=None):
    exit(1)
    meta_types = ds_context.get_meta_types_by_scope(scope)
    domains = ds_context.get_domains_by_scope(scope)
    rdc_adjacency_matrix_dict = {}
    if local_data.shape[0] > max_sampling_threshold_cols:
        local_data_sample = local_data[np.random.randint(local_data.shape[0], size=max_sampling_threshold_cols), :]
        rdc_adjacency_matrix = rdc_calculate(local_data_sample,
                                             meta_types,
                                             domains,
                                             k=k,
                                             s=s,
                                             # ohe=True,
                                             non_linearity=non_linearity,
                                             n_jobs=n_jobs,
                                             rand_gen=rand_gen)
    elif local_data.shape[0] > 1:
        rdc_adjacency_matrix = rdc_calculate(local_data,
                                             meta_types,
                                             domains,
                                             k=k,
                                             s=s,
                                             # ohe=True,
                                             non_linearity=non_linearity,
                                             n_jobs=n_jobs,
                                             rand_gen=rand_gen)
    else:
        return None

    for i in range(len(scope)):
        rdc_adjacency_matrix_dict[scope[i]] = rdc_adjacency_matrix[i]
    print(rdc_adjacency_matrix_dict)
    return rdc_adjacency_matrix_dict


def rdc_calculate(local_data, meta_types, domains, k=None, s=1.0 / 6.0, non_linearity=np.sin, n_jobs=-1, rand_gen=None):
    rdc_adjacency_matrix = rdc_test(
        local_data, meta_types, domains, k=k, s=s, non_linearity=non_linearity, n_jobs=n_jobs, rand_gen=rand_gen
    )
    rdc_adjacency_matrix[np.isnan(rdc_adjacency_matrix)] = 0
    # print('rdc_adjacency_matrix:', rdc_adjacency_matrix)
    return rdc_adjacency_matrix


def create_custom_leaf(data, ds_context, scope, data_id=None, rdc_adjacency_matrix_dict=None):
    """
    Adapted leafs for cardinality SPN. Either categorical or identityNumeric leafs.
    unique_vals_ids: the structure used to store bitmaps
    """
    idx = scope[0]
    meta_type = ds_context.meta_types[idx]
    unique_vals_ids = {}
    if meta_type == MetaType.REAL:
        assert len(scope) == 1, "scope for more than one variable?"

        unique_vals, counts = np.unique(data[:, 0], return_counts=True)

        if hasattr(ds_context, 'no_compression_scopes') and idx not in ds_context.no_compression_scopes and \
                len(unique_vals) > MAX_UNIQUE_LEAF_VALUES:
            # if there are too many unique values build identity leaf with histogram representatives
            hist, bin_edges = np.histogram(data[:, 0], bins=MAX_UNIQUE_LEAF_VALUES, density=False)
            logger.debug(f"\t\tDue to histograms leaf size was reduced "
                         f"by {(1 - float(MAX_UNIQUE_LEAF_VALUES) / len(unique_vals)) * 100:.2f}%")
            unique_vals = bin_edges[:-1]
            print(len(unique_vals))
            probs = hist / data.shape[0]
            lidx = len(probs) - 1

            assert len(probs) == len(unique_vals)

            unique_vals_ids.clear()
            for i in range(len(unique_vals)):
                sta = bin_edges[i]
                end = bin_edges[i+1]
                if i < len(unique_vals) - 1:
                    temp_id = np.argwhere(np.logical_and(data[:, 0] >= sta, data[:, 0] < end))[:, 0]
                else:
                    temp_id = np.argwhere(np.logical_and(data[:, 0] >= sta, data[:, 0] <= end))[:, 0]
                unique_vals_ids[sta] = RoaringBitmap(temp_id)

        else:
            for x in unique_vals:
                temp_id = np.argwhere(data[:, 0] == x)[:, 0]
                unique_vals_ids[x] = RoaringBitmap(np.array([data_id[i] for i in temp_id]))

            probs = np.array(counts, np.float64) / len(data[:, 0])
            lidx = len(probs) - 1

        null_value = ds_context.null_values[idx]
        leaf = IdentityNumericLeaf(unique_vals, probs, null_value, scope, cardinality=data.shape[0], unique_vals_ids=unique_vals_ids, rdc_adjacency_matrix_dict=rdc_adjacency_matrix_dict)

        return leaf

    elif meta_type == MetaType.DISCRETE:
        unique, counts = np.unique(data[:, 0], return_counts=True)
        # +1 because of potential 0 value that might not occur
        sorted_counts = np.zeros(len(ds_context.domains[idx]) + 1, dtype=np.float64)
        for i, x in enumerate(unique):
            sorted_counts[int(x)] = counts[i]
        p = sorted_counts / data.shape[0]
        null_value = ds_context.null_values[idx]
        # print(p, null_value, scope)
        for x in unique:
            temp_id = np.argwhere(data[:, 0] == x)[:, 0]
            unique_vals_ids[x] = RoaringBitmap(np.array([data_id[i] for i in temp_id]))
                
        node = Categorical(p, null_value, scope, cardinality=data.shape[0], unique_vals_ids=unique_vals_ids)

        return node


def get_splitting_functions(max_sampling_threshold_rows, max_sampling_threshold_cols, cols, rows, ohe, threshold,
                            rand_gen, n_jobs):
    from spn.algorithms.splitting.Clustering import get_split_rows_TSNE, get_split_rows_GMM
    from spn.algorithms.splitting.PoissonStabilityTest import get_split_cols_poisson_py
    from spn.algorithms.splitting.RDC import get_split_rows_RDC_py
    rdc_adjacency_matrix = None
    if isinstance(cols, str):

        if cols == "rdc":
            split_cols = get_split_cols_RDC_py(max_sampling_threshold_cols=max_sampling_threshold_cols,
                                               threshold=threshold,
                                               rand_gen=rand_gen, ohe=ohe, n_jobs=n_jobs)
        elif cols == "poisson":
            split_cols = get_split_cols_poisson_py(threshold, n_jobs=n_jobs)
        else:
            raise AssertionError("unknown columns splitting strategy type %s" % str(cols))
    else:
        split_cols = cols

    if isinstance(rows, str):

        if rows == "rdc":
            split_rows = get_split_rows_RDC_py(rand_gen=rand_gen, ohe=ohe, n_jobs=n_jobs)
        elif rows == "kmeans":
            split_rows = get_split_rows_KMeans(max_sampling_threshold_rows=max_sampling_threshold_rows)
        elif rows == "tsne":
            split_rows = get_split_rows_TSNE()
        elif rows == "gmm":
            split_rows = get_split_rows_GMM()
        else:
            raise AssertionError("unknown rows splitting strategy type %s" % str(rows))
    else:
        split_rows = rows
    return split_cols, split_rows


# noinspection PyPep8Naming
def get_split_rows_KMeans(max_sampling_threshold_rows, n_clusters=2, pre_proc=None, ohe=False, seed=17):
    # noinspection PyPep8Naming
    def split_rows_KMeans(local_data, ds_context, scope, local_data_id=None):
        data = preproc(local_data, ds_context, pre_proc, ohe)

        import warnings
        from sklearn.exceptions import ConvergenceWarning

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            if data.shape[0] > max_sampling_threshold_rows:
                data_sample = data[np.random.randint(data.shape[0], size=max_sampling_threshold_rows), :]

                kmeans = KMeans(n_clusters=n_clusters, random_state=seed)
                clusters = kmeans.fit(data_sample).predict(data)
            else:
                kmeans = KMeans(n_clusters=n_clusters, random_state=seed)
                clusters = kmeans.fit_predict(data)

        cluster_centers = kmeans.cluster_centers_

        unique_clusters, result_ids = np.unique(clusters), []
        for u_c in unique_clusters:
            temp_id = [local_data_id[i] for i, x in enumerate(clusters) if x == u_c]
            result_ids.append(temp_id)

        result = split_data_by_clusters(local_data, clusters, scope, rows=True)

        return result, cluster_centers.tolist(), result_ids

    return split_rows_KMeans


# noinspection PyPep8Naming
def get_split_cols_RDC_py(max_sampling_threshold_cols=10000, threshold=0.3, ohe=True, k=10, s=1 / 6,
                          non_linearity=np.sin,
                          n_jobs=-2, rand_gen=None):
    from spn.algorithms.splitting.RDC import split_data_by_clusters

    def split_cols_RDC_py(local_data, ds_context, scope):
        meta_types = ds_context.get_meta_types_by_scope(scope)
        domains = ds_context.get_domains_by_scope(scope)
        rdc_adjacency_matrix_dict = {}

        if local_data.shape[0] > max_sampling_threshold_cols:
            local_data_sample = local_data[np.random.randint(local_data.shape[0], size=max_sampling_threshold_cols), :]
            rdc_adjacency_matrix = rdc_calculate(local_data_sample,
                meta_types,
                domains,
                k=k,
                s=s,
                # ohe=True,
                non_linearity=non_linearity,
                n_jobs=n_jobs,
                rand_gen=rand_gen)
            clusters = getIndependentRDCGroups_py(
                local_data_sample,
                threshold,
                meta_types,
                domains,
                k=k,
                s=s,
                # ohe=True,
                non_linearity=non_linearity,
                n_jobs=n_jobs,
                rand_gen=rand_gen,
            )
            for i in range(len(scope)):
                rdc_adjacency_matrix_dict[scope[i]] = rdc_adjacency_matrix[i]
            return split_data_by_clusters(local_data, clusters, scope, rows=False), rdc_adjacency_matrix_dict
        else:
            rdc_adjacency_matrix = rdc_calculate(local_data,
                          meta_types,
                          domains,
                          k=k,
                          s=s,
                          # ohe=True,
                          non_linearity=non_linearity,
                          n_jobs=n_jobs,
                          rand_gen=rand_gen)
            clusters = getIndependentRDCGroups_py(
                local_data,
                threshold,
                meta_types,
                domains,
                k=k,
                s=s,
                # ohe=True,
                non_linearity=non_linearity,
                n_jobs=n_jobs,
                rand_gen=rand_gen,
            )
            for i in range(len(scope)):
                rdc_adjacency_matrix_dict[scope[i]] = rdc_adjacency_matrix[i]
            return split_data_by_clusters(local_data, clusters, scope, rows=False), rdc_adjacency_matrix_dict

    return split_cols_RDC_py
