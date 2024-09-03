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
    parser = argparse.ArgumentParser(description='Program execution script')
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

