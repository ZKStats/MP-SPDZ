# MPCStats Benchmarking

## Preparation

### Protocols definitions
First specify which protocols to use for benchmarking in:
`./protocols.py`

For each protocol used, associated `.x` file needs to be built. To do that, call `./build_vm.py`

### Datasets for benchmarking
Next create the datasets to be used for benchmarking in `./datasets`.
The datasets should be in CSV format without a header line.
datasets whose names start with '_' are ignored.

#### Dataset generation script
You can use `./dataset_gen.py` to randomly generate datasets for benchmarking purposes.

### Computation defintions
Lastly, define the computations to be benchmarked in `./computation_defs/templates`.

By executing `./build_comp_defs.py`, computaion definition instances for all dataset and template combinations will be created in the `./computations_defs` directory.

Computation definitions whose names start with '_' are ignored.

## Running the benchmark
Execute the `./driver.py` to run the benchmarks and output the reulsts a CSV to stdout.

