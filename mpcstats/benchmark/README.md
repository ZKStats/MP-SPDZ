# MPCStats Benchmarking

## Preparation

### Protocols definitions
First specify which protocols to use for benchmarking in:
`./protocols.py`

For each protocol used, the associated `.x` file needs to be built. To do this, run `./gen_vms.py`

### Datasets for benchmarking
Next create the datasets to be used for benchmarking in `./datasets`.
The datasets should be in CSV format without a header line.
datasets whose names start with '_' are ignored.

#### Dataset generation script
You can use `./gen_dataset.py` to randomly generate datasets for benchmarking purposes.

### Computation defintions
Lastly, define the computations to be benchmarked in `./computation_defs/templates`.

By executing `./gen_comp_defs.py`, computaion definition instances for all dataset and template combinations will be created in the `./computations_defs` directory.

Computation definitions whose names start with '_' are ignored.

### Setting up ssl
On party 0 host, in `mpcstats/benchmark` directory, run:

```
../../Scripts/setup-ssl.sh 3
```

Then, copy `Player-Data/P{0,1,2}.pem` to the other party hosts as explained below.

```
The certificates should be the same on every host. Also make sure that it's still valid. Certificates generated with `Scripts/setup-ssl.sh` expire after a month.
```

```bash
scp pse-eu:'MP-SPDZ/mpcstats/benchmark/Player-Data/*.pem' .
scp *.pem pse-us:MP-SPDZ/mpcstats/benchmark/Player-Data
scp *.pem pse-asia:MP-SPDZ/mpcstats/benchmark/Player-Data
```

## Running the benchmark
Execute the `./driver.py [scenario ID]` to run the benchmarks and output the results as a CSV to stdout.

To get the list of secnario IDs, run:

```
./driver.sh -h
```

### Setting up a remote machine
Assuming a Ubuntu 24.04, x86, 64-bit instance

- Install necessary libraries
```
sudo apt update
sudo apt-get install -y automake build-essential clang cmake git libboost-all-dev libgmp-dev libntl-dev libsodium-dev libssl-dev libtool python3
```

- Install MP-SPDZ
```
git clone https://github.com/exfinen/MP-SPDZ.git
cd MP-SPDZ
git checkout benchmarker
```

- Generate ssl keys and distribute to all parties

```
cd MP-SPDZ/mpcstats/benchmark
../../Scripts/setup-ssl.sh 3
```

Then copy `PlayerData/P*.pem` and `PlayerData/P*.key` to the same location in other instances

- Make parties accssible to other parties without password

1. On each party instance, create `~/.ssh/config` of the following contents:

```
Host p0
  HostName 3.107.77.187
  User ubuntu
  IdentityFile ~/party0.pem
  IdentitiesOnly yes
  Port 22
Host p1
  HostName 3.26.224.96
  User ubuntu
  IdentityFile ~/party1.pem
  IdentitiesOnly yes
  Port 22
Host p2
  HostName 3.107.161.167
  User ubuntu
  IdentityFile ~/party2.pem
  IdentitiesOnly yes
  Port 22
```

2. Copy `.pem` files to the home directory of each party instance

