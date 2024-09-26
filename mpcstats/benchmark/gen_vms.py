#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'

import sys
sys.path.append(f'{repo_root}/mpcstats/benchmark')

import subprocess
import os
from protocols import all_protocols

config_mine = repo_root / 'CONFIG.mine'

for _, program, _, _ in all_protocols:
    # special handling for spdz2k
    config_mine_content = 'MOD = -DRING_SIZE=128' if program == 'spdz2k-party.x' else ''
    print(f'Compiling {program} w/ {config_mine_content}...')

    with open(config_mine, 'w') as file:
        file.write(config_mine_content)

    cmd = ['make', f'-j{os.cpu_count()}', program]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    if res.returncode != 0:
        print(f'--> Failed w/ return code {res.returncode}. {res.stderr}')

