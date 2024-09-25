#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'

import sys
sys.path.append(f'{repo_root}/mpcstats/benchmark')

import subprocess
import os
from protocols import all_protocols

for _, program, _, _ in all_protocols:
    print(f'Compiling {program}...')

    cmd = ['make', f'-j{os.cpu_count()}', program]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, env=env)

    if res.returncode != 0:
        print(f'--> Failed w/ return code {res.returncode}. {res.stderr}')

