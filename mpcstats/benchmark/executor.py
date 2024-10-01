#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import execute_silently, exec_subprocess, DIMENTION_FILE, read_script
from output_parser import parse_execution_output
from constants import PROG_NAME, PROTOCOL
from Compiler.types import sfix, Matrix

import argparse
import re
import json
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Program execution script')
    parser.add_argument(
        'protocol',
        type=str, 
        help='MPC protocol',
    )
    parser.add_argument(
        'num_parties',
        type=int, 
        help='Number of participating parties',
    )
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
    parser.add_argument(
        '--remote',
        type=int,
        help='Party number in remote execution',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show output from MPC script',
    )
    return parser.parse_args()

args = parse_args()

# inject computation definition script into this script
script = read_script(args.file)
exec(script)

# make sure the number of parties in computation and arguments are consistent
if NUM_PARTIES != args.num_parties:
    raise f'NUM_PARTIES is {NUM_PARTIES}, args.num_parties is {args.num_parties}'

prepare_data() # from computation definition script

# execute the injected computation
if args.remote is not None:
    vm = str(repo_root / f'{args.protocol}-party.x')
    cmd = f'{vm} -N {args.num_parties} -ip HOSTS -p {args.remote} {args.name}'
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(repo_root)

    env = f'LD_LIBRARY_PATH={str(repo_root)}'
else:
    mpc_script = str(repo_root / 'Scripts' / f'{args.protocol}.sh')
    cmd = f'PLAYERS={args.num_parties} {mpc_script} {args.name}'
    env = None

output = exec_subprocess(cmd, env)
out_obj = parse_execution_output(output)
out_obj[PROTOCOL] = args.protocol
out_obj[PROG_NAME] = args.name

if args.verbose:
    print(output)

print(json.dumps(out_obj))
