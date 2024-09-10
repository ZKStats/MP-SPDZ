#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
import re
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import execute_silently, execute_computation, Protocols, ProtocolsType, DIMENTION_FILE
from output_parser import parse_execution_output
from Compiler.types import sfix, Matrix

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
        '--verbose',
        action='store_true',
        help='Show output from MPC script',
    )
    return parser.parse_args()

args = parse_args()

# inject computation definition script into this script
if args.file is None:
     script = sys.stdin.read()
else:
    # assumes that file is already opened
    try:
        script = args.file.read()
    finally:
        args.file.close()
exec(script)

prepare_data() # from computation definition script

# execute the injected computation
mpc_script = str(repo_root / 'Scripts' / f'{args.protocol}.sh')

output = execute_computation(
    NUM_PARTIES, # from computation definition script
    mpc_script,
    args.name,
)
out_obj = parse_execution_output(output)

if args.verbose:
    print(output)

print(out_obj)
