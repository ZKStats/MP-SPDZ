#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
import re
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import execute_silently, execute_computation, Protocols, ProtocolsType

import argparse
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Program execution script')
    now = datetime.now().strftime('%Y%m%d_%H%M%S')

    parser.add_argument(
        'protocol',
        type=str, 
        choices=Protocols, 
        help='MPC protocol',
    )
    parser.add_argument(
        'name',
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
    parser.add_argument(
        '--num-parties',
        type=int,
        default=3,
        help='Number of parties participating the computation',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show output from MPC script',
    )
    return parser.parse_args()

args = parse_args()

if args.file is not None:
    pass

mpc_script = str(repo_root / 'Scripts' / f'{args.protocol}.sh')

output = execute_computation(
    args.num_parties,
    mpc_script,
    args.name,
)
if args.verbose:
    print(output)
