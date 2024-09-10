#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
import os
import re
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from common_lib import compile_computation, execute_silently
from Compiler.library import print_ln
from timeit import timeit
from datetime import datetime
import argparse
import json
from typing import Any

def parse_args() -> Any:
    parser = argparse.ArgumentParser(description='Compile script')
    now = datetime.now().strftime('%Y%m%d_%H%M%S')

    parser.add_argument(
        '--name',
        type=str,
        default=f'computation',
        help='Name of the computation',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show output from Comipler module',
    )
    parser.add_argument(
        '--file',
        type=argparse.FileType('r'),
        default=None,
        help='Computation definition file. If not specified, the definition will be read from stdin',
    )
    parser.add_argument(
        '--edabit',
        action='store_true',
        help='Use edaBit',
    )
    return parser.parse_args()

args = parse_args()

# inject computation definition script
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

# compile the computation
def f():
    flags = []
    if args.edabit:
        flags.append('--edabit')
    compile_computation(args.name, computation, flags)

def g():
    return timeit(f, number=1)

time_elapsed = g() if args.verbose else execute_silently(g)

# build the json output and print
prog_name_re = re.compile(rf'^{args.name}-\d+\.bc$')
bytecode_dir = benchmark_dir / 'Programs' / 'Bytecode'

files = [
    { 'name': file.name, 'size': file.stat().st_size } for file
    in bytecode_dir.rglob(f'{args.name}-*.bc')
    if prog_name_re.match(file.name)
]

output = {
    'program_name': args.name,
    'compilation_time': time_elapsed,
    'bytecodes': files,
}

print(json.dumps(output))
