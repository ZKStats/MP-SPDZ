#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
datasets_dir = repo_root / 'mpcstats' / 'benchmark' / 'datasets'

import os
import shutil
import random
from typing import Any

import argparse

def parse_args() -> Any:
    parser = argparse.ArgumentParser(description='Dataset gen script')
    parser.add_argument(
        'num_columns',
        type=int,
        help='Number of columns',
    )
    parser.add_argument(
        'num_rows',
        type=int,
        help='Number of rows',
    )
    parser.add_argument(
        '--mean',
        type=float,
        default=0,
        help='Mean of normal distribution',
    )
    parser.add_argument(
        '--stddev',
        type=float,
        default=1,
        help='Standard deviation of normal distribution',
    )
    parser.add_argument(
        'dir_name',
        type=str,
        help='Directory where the dataset file is created',
    )
    return parser.parse_args()

args = parse_args()

dataset_dir = datasets_dir / args.dir_name
if dataset_dir.exists():
    shutil.rmtree(dataset_dir)
dataset_dir.mkdir()

with open(dataset_dir / 'data.csv', 'w') as file:
    for _row in range(args.num_rows):
        nums = [random.gauss(args.mean, args.stddev) for _ in range(args.num_columns)]
        line = ','.join([str(n) for n in nums])
        file.write(f'{line}\n')

