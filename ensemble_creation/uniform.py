import logging
from aqp_spn.aqp_spn import AQPSPN
from data_preparation.join_data_preparation import JoinDataPreparator
from ensemble_compilation.spn_ensemble import SPNEnsemble

logger = logging.getLogger(__name__)

def create_uniform_ensemble(schema, hdf_path, sample_size, ensemble_path, dataset, max_table_data, post_sampling_factor):
    meta_data_path = hdf_path + '/meta_data.pkl'
    prep = JoinDataPreparator(meta_data_path, schema, max_table_data=max_table_data)
    spn_ensemble = SPNEnsemble(schema)

    logger.info(f"Creating uniform ensemble.")

    for table_obj in schema.tables:
        logger.info(f"Generating Uniform SPN for {table_obj.table_name}.")
        # Generate samples just to get domain/unique values
        df_samples, meta_types, null_values, full_join_est = prep.generate_n_samples(sample_size,
                                                                                     single_table=table_obj.table_name,
                                                                                     post_sampling_factor=post_sampling_factor)

        # learn spn
        aqp_spn = AQPSPN(meta_types, null_values, full_join_est, schema, None, full_sample_size=len(df_samples),
                         table_set={table_obj.table_name}, column_names=list(df_samples.columns),
                         table_meta_data=prep.table_meta_data)
        
        logger.info(f"Building uniform tree structure...")

        aqp_spn.learn_uniform(df_samples.values, sum_fanout=8, product_fanout=2, max_depth=4,leaf_fanout=10)
        
        spn_ensemble.add_spn(aqp_spn)


    ensemble_path += '/ensemble_single_uniform_' + dataset +'_' + str(min(sample_size, len(df_samples))) + '.pkl'
    logger.info(f"Saving ensemble to {ensemble_path}")
    spn_ensemble.save(ensemble_path)
