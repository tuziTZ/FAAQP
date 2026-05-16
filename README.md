# FAAQP

FAAQP is a data-driven AQP method that achieves state-of-the-art performance in approximate query processing (AQP). The structure of BSPN is an extension of existing SPN-based methods. This is a version of BSPN based on RSPN (https://github.com/DataManagementLab/deepdb-public/tree/master).

Hanbing Zhang, Yinan Jing, Zhenying He, Kai Zhang, and X. Sean Wang: "FAAQP: Fast and Accurate Approximate Query Processing based on Bitmap-augmented Sum-Product Network", SIGMOD 2025.

# Setup
All experiments are conducted on a Linux machine with Intel Xeon Gold 5215 CPU, Nvidia RTX3080 GPU, 160GB RAM, and 3.3TB HDD disk.
Tested with python3.7 and python3.8
```
git clone git@github.com:DogeWang/SPNPP.git
cd SPNPP
sudo apt install -y libpq-dev gcc python3-dev
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
install roaringbitmap from https://github.com/andreasvc/roaringbitmap
```

For python3.8: Sometimes spflow fails, in this case remove spflow from requirements.txt, install them and run
```
pip3 install spflow --no-deps
```

# AQP
## Flights pipeline
Download data (5 million tuples) from https://www.transtats.bts.gov/Homepage.asp. You can also download the data from https://pan.baidu.com/s/1c31bBx8DF6QJ6boYV8DWAg?pwd=2xyn by using the code "2xyn".

Generate hdf files from csvs.
```
python3 maqp.py --generate_hdf
    --dataset flights_origin
    --csv_seperator ,
    --csv_path ../flights-benchmark
    --hdf_path ../flights-benchmark/gen_hdf
```

Learn the naive BSPN model.
```
python3 maqp.py --generate_ensemble
    --dataset flights_origin
    --samples_per_spn 10000000
    --ensemble_strategy single
    --hdf_path ../flights-benchmark/gen_hdf
    --ensemble_path ../flights-benchmark/spn_ensembles
    --rdc_threshold 0.3
    --post_sampling_factor 10
```

Learn the BSPN with given storage budget.
```
input the path of the naive BSPN model and the output path of the BSPN model with given storage budget in the utils/storage_control.py
the default storage budget is set at 10% of the underlying data
python3 utils/storage_control.py
```

Learn the BSPN with BMS.
```
input the path of the BSPN model and the output path of the BSPN model with BMS in the utils/histogram_control.py
the default threshold is set at 100
python3 utils/histogram_control.py
```

Compute ground truth by using PostgreSQL.
To get the ground truth, you should store the flights_origin.csv in PostgreSQL. You can use "\COPY flights(YEAR_DATE, UNIQUE_CARRIER, ORIGIN, ORIGIN_STATE_ABR, DEST, DEST_STATE_ABR, DEP_DELAY, TAXI_OUT, TAXI_IN, ARR_DELAY, AIR_TIME, DISTANCE) from '/tmp/dataset.csv' WITH CSV HEADER;" to do this.
Then
```
python3 maqp.py --aqp_ground_truth
    --dataset flights_origin
    --query_file_location ./benchmarks/flights/sql/aqp_test_queries.sql
    --target_path ./benchmarks/flights/aqp_test_queries_ground_truth.pkl
    --database_name flights_origin
```

Evaluate the AQP queries using the naive BSPN model. If you want to test the different version of BSPN (such as BSPN with storage budget), please change the ../flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_RoaringBitmap.pkl.
```
python3 maqp.py --evaluate_aqp_queries
    --dataset flights_origin
    --target_path ./baselines/aqp/results/deepDB/aqp_test_queries_BSPN.csv
    --ensemble_location ../flights-benchmark/spn_ensembles/ensemble_single_flights_origin_5000000_RoaringBitmap.pkl
    --query_file_location ./benchmarks/flights/sql/aqp_test_queries.sql
    --ground_truth_file_location ./benchmarks/flights/aqp_test_queries_ground_truth.pkl
```

## Appian pipeline
Prepare the Appian CSVs into FAAQP-ready files without headers. This keeps the repository reader unchanged and writes the transformed files to `./appian-benchmark/prepared`.
```
python3 utils/prepare_appian_dataset.py \
    --input_dir ./appian-benchmark \
    --output_dir ./appian-benchmark/prepared \
    --overwrite
```

All validation and benchmark runs below use the Docker container `aqp-mpc-pbspn`.

Generate HDF files.
```
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && python3 maqp.py --generate_hdf --dataset appian --csv_seperator , --csv_path ./appian-benchmark/prepared --hdf_path ./appian-benchmark/gen_hdf'
```

Run a small ensemble smoke test.
```
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && python3 maqp.py --generate_ensemble --dataset appian --ensemble_strategy single --samples_per_spn 50000 50000 50000 50000 --post_sampling_factor 1 1 1 1 --hdf_path ./appian-benchmark/gen_hdf --ensemble_path ./appian-benchmark/spn_ensembles_smoke'
```

Run the normal single-ensemble training.
```
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && python3 maqp.py --generate_ensemble --dataset appian --ensemble_strategy single --samples_per_spn 1000000 1000000 500000 500000 --post_sampling_factor 5 5 2 1 --hdf_path ./appian-benchmark/gen_hdf --ensemble_path ./appian-benchmark/spn_ensembles'
```

Create and load the PostgreSQL `appian` database from the prepared CSVs.
```
docker exec aqp-mpc-pbspn sh -lc 'su postgres -c "createdb appian"'
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && su postgres -c "psql -d appian -f benchmarks/appian/setup-sql/schema.sql"'
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && su postgres -c "psql -d appian -f benchmarks/appian/setup-sql/load_prepared.sql"'
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && su postgres -c "psql -d appian -f benchmarks/appian/setup-sql/indexes.sql"'
```

Compute PostgreSQL ground truth for the FAAQP-compatible Appian workload.
```
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && python3 maqp.py --aqp_ground_truth --dataset appian --query_file_location ./benchmarks/appian/sql/appian_all.sql --target_path ./benchmarks/appian/appian_all_ground_truth.pkl --database_name appian'
```

Evaluate the Appian workload with the trained ensemble.
```
docker exec aqp-mpc-pbspn sh -lc 'cd /workspace/FAAQP && mkdir -p ./appian-benchmark/results && python3 maqp.py --evaluate_aqp_queries --dataset appian --target_path ./appian-benchmark/results/appian_all_model_based.csv --ensemble_location ./appian-benchmark/spn_ensembles/ensemble_single_appian_800000_RoaringBitmap.pkl --query_file_location ./benchmarks/appian/sql/appian_all.sql --ground_truth_file_location ./benchmarks/appian/appian_all_ground_truth.pkl'
```
