from pathlib import Path
repo_root = Path(__file__).parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'
player_data_dir = benchmark_dir / 'Player-Data'
datasets_dir = benchmark_dir / 'datasets'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from Compiler.compilerLib import Compiler
from Compiler.types import sfix, Matrix
from Compiler.library import print_ln
import subprocess
import config
import os
import re
import json
from typing import Callable, Any, Literal, TextIO
from dataclasses import dataclass

# TODO generate list from type definition
ProtocolsType = Literal['semi', 'mascot']
Protocols = ['semi', 'mascot']

DIMENTION_FILE = player_data_dir / 'file-dimentions.txt'
DIMENTION_FILE_SEP = ' '

@dataclass
class Dimention:
    rows: int
    cols: int

    def num_elements(self):
        return self.rows * self.cols

@dataclass
class ComputationOutput:
    result: str

    def to_object(self) -> Any:
        return {
            'Result': self.result,
        }
    def __str__(self) -> str:
        return json.dumps(self.to_object())

def create_party_data_files(dataset_file: Path, num_parties: int) -> None:
    if not dataset_file.exists():
        raise FileNotFoundError(f'{dataset_file} not found')

    try:
        dims = open(DIMENTION_FILE, 'w')
        party_files = [open(player_data_dir / f'Input-P{i}-0', 'w') for i in range(num_parties)]
        file = dataset_file.open('r')

        curr_party = 0
        num_rows = [0] * num_parties
        num_columns = [None] * num_parties

        # read from dataset_file and create party data files
        # keeping track of the dimention of each file
        with open(dataset_file) as file:
            while line := file.readline():
                toks = [tok.strip() for tok in line.split(',')]
                if num_columns[curr_party] is None:
                    num_columns[curr_party] = len(toks)

                line = ' '.join(toks)
                party_files[curr_party].write(f'{line}\n')

                num_rows[curr_party] += 1
                curr_party = (curr_party + 1) % num_parties

        # write dimentions of party files to file
        for i in range(num_parties):
            dims.write(f'{num_rows[i]}{DIMENTION_FILE_SEP}{num_columns[i]}\n')

    finally:
        for f in party_files:
            f.close()
        dims.close()

def load_file_dimentions() -> list[Dimention]:
    if not Path(DIMENTION_FILE).is_file():
        raise FileNotFoundError(f'{DIMENTION_FILE} not found')
    dims = []
    with open(DIMENTION_FILE) as f:
        while (line := f.readline().strip()) is not None:
            if line == '': # if the last line
                return dims
            toks = line.split(DIMENTION_FILE_SEP) 
            rows, cols = toks
            dim = Dimention(int(rows), int(cols))
            dims.append(dim)

# has to be called from inside computation
# assumes that DIMENTION_FILE has already been created
def load_party_data_files(num_parties: int) -> list[Matrix]:
    dims = load_file_dimentions()
    ms = []
    for i in range(num_parties):
        with open(player_data_dir / f'Input-P{i}-0') as f:
            dim = dims[i]

            m = Matrix(dim.rows, dim.cols, sfix)
            for row in range(dim.cols):
                for col in range(dim.cols):
                    m[row][col] = sfix.get_input_from(i)

            ms.append(m)
    return ms

def get_aggr_party_data_vec(num_parties: int, row_index: int) -> list[sfix]:
    # load party data into matrices
    ms = load_party_data_files(num_parties)

    # aggregate matrix row of all parties
    vec = []
    for party_id, m in enumerate(ms):
        row = [m[row_index][i] for i in range(m.shape[1])]
        vec[:] += row[:]

    return vec

def compile_computation(
    name: str,
    computation: Callable[[], None],
    cfg: Any = config.DefaultMPSPDZSetting(),
) -> None:
    '''
    Compiles computation function and generates:
    - ./Programs/Schedules/{name}.sch
    - ./Programs/Bytecode/{name}-0.bc
    in the current directory
    '''
    def init_and_compute():
        sfix.round_nearest = cfg.round_nearest
        sfix.set_precision(cfg.f, cfg.k)
        computation()

    compiler = Compiler()
    compiler.register_function(name)(init_and_compute)

    # temporarily clear the command line arguments passed to the caller script
    # while executing compiler.compile_func
    # since it affects how compile.compile_func works
    bak = sys.argv
    sys.argv = [sys.argv[0]]
    compiler.compile_func()
    sys.argv = bak

def execute_computation(
    num_parties: int,
    mpc_script: str,
    name: str,
) -> str:
    cmd = f'PLAYERS={num_parties} {mpc_script} {name}'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        return res.stdout

    except subprocess.CalledProcessError as e:
        raise Exception(f'Executing MPC failed ({e.returncode}): stdout: {e.stdout}, stderr: {e.stderr}')

def parse_computation_output(output: str) -> ComputationOutput:
    # TODO extract other information as well
    result = None

    for line in output.split('\n'):
        if result is None:
            m = re.match(r'^Result: (.*)$', line)
            if m:
                result = m.group(1)

    return ComputationOutput(result)

def execute_silently(f: Callable[[], None]) -> Any:
    stdout_bak = sys.stdout

    # redirect stdout to /dev/null
    sys.stdout = open(os.devnull, 'w')

    try:
        return f()
    finally:
        sys.stdout.close()
        sys.stdout = stdout_bak

def write_result(value: Any) -> None:
    print_ln('Result: %s', value)
