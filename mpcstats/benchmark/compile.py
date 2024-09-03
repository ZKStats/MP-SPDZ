#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
import re
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import compile_computation
from Compiler.library import print_ln
from timeit import timeit
from datetime import datetime

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Compile script')
    now = datetime.now().strftime('%Y%m%d_%H%M%S')

    parser.add_argument(
        '--name',
        type=str,
        default=f'computation',
        help='Name of the computation',
    )
    parser.add_argument(
        '--file',
        type=argparse.FileType('r'),
        default=None,
        help='Computation definition file. If not specified, the definition will be read from stdin',
    )
    return parser.parse_args()

args = parse_args()

if args.file is None:
    computation_def = sys.stdin.read()
else:
    computation_def = args.file.read()
    args.file.close()

exec(computation_def)

def f():
    compile_computation(args.name, computation)

# print compilation time
time_elapsed = timeit(f, number=1)
print(f'Compilation Time: {time_elapsed}')

# print compiled bytecodes with size 
prog_name_re = re.compile(rf'^{args.name}-\d+\.bc$')
bytecode_dir = benchmark_dir / 'Programs' / 'Bytecode'

files = [
    (file.name, file.stat().st_size) for file
    in bytecode_dir.rglob(f'{args.name}-*.bc')
    if prog_name_re.match(file.name)
]
print(f'Bytecodes: {files}')
