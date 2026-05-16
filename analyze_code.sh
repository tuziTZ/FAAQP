#!/bin/sh
source ~/.bashrc 
conda activate python37
#nohup python3 -u maqp.py --generate_ensemble --dataset flights_origin --samples_per_spn 10000000 --ensemble_strategy single --hdf_path ../flights-benchmark/gen_hdf --ensemble_path ../flights-benchmark/spn_ensembles --rdc_threshold 0.3 --post_sampling_factor 10
#python3 maqp.py --aqp_ground_truth --dataset flights_origin --query_file_location ./benchmarks/flights/sql/aqp_queries.sql --target_path ./benchmarks/flights/ground_truth_origin.pkl --database_name flights_test
# nohup python3 -u maqp.py --evaluate_aqp_queries --dataset flights_origin --target_path ./baselines/aqp/results/deepDB/flights_origin_model_based.csv --ensemble_location ../flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000.pkl --query_file_location ./benchmarks/flights/sql/aqp_queries.sql --ground_truth_file_location ./benchmarks/flights/ground_truth_origin.pkl > deepdb.out &
python3 maqp.py --evaluate_aqp_queries --dataset flights_origin --target_path ./baselines/aqp/results/deepDB/flights_origin_model_based.csv --ensemble_location ../flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000.pkl --query_file_location ./benchmarks/flights/sql/aqp_queries.sql --ground_truth_file_location ./benchmarks/flights/ground_truth_origin.pkl 
