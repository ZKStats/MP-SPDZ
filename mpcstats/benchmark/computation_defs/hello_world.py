from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from Compiler.types import sfix
from Compiler.library import print_ln
from common_lib import create_party_data_files, load_party_data_files, write_result

NUM_PARTIES = 3

def prepare_data():
    datasets_dir = benchmark_dir / 'datasets'
    dataset_file = datasets_dir / 'wine' / 'wine.data.txt'
    create_party_data_files(dataset_file, NUM_PARTIES)

def computation():
    ms = load_party_data_files(NUM_PARTIES)
    all_elems = []

    selected_row = 0

    for party_id, m in enumerate(ms):
        row = [m[selected_row][i] for i in range(m.shape[1])]
        all_elems[:] += row[:]

    total = sum(all_elems)
    write_result(total.reveal())

