#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
import re
import json
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import execute_silently, exec_subprocess, Protocols, ProtocolsType, DIMENTION_FILE, read_script
from output_parser import parse_execution_output
from Compiler.types import sfix, Matrix

import argparse
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Program execution script')
    parser.add_argument(
        'protocol',
        type=str, 
        choices=Protocols, 
        help='MPC protocol',
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
        '--verbose',
        action='store_true',
        help='Show output from MPC script',
    )
    return parser.parse_args()

args = parse_args()

# inject computation definition script into this script
script = read_script(args.file)
exec(script)

prepare_data() # from computation definition script

# execute the injected computation
mpc_script = str(repo_root / 'Scripts' / f'{args.protocol}.sh')
cmd = f'PLAYERS={NUM_PARTIES} {mpc_script} {args.name}'
output = exec_subprocess(cmd)

out_obj = parse_execution_output(output)
out_obj['protocol'] = args.protocol
out_obj['prog_name'] = args.name

if args.verbose:
    print(output)

print(json.dumps(out_obj))
