#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import argparse
import subprocess
import os
import time
from typing import List, Literal
import json

# TODO generate list from type definition
MemoryFieldsType = Literal['sz', 'rss']
MemoryFields = ['sz', 'rss']

ProtocolsType = Literal['semi', 'mascot']
Protocols = ['semi', 'mascot']

os.environ['PATH'] += os.pathsep + str(benchmark_dir)
page_size = os.sysconf("SC_PAGE_SIZE")  # in bytes

def exec_ps(pid: int, field: MemoryFieldsType) -> int:
    if os.name == 'posix':
        res = subprocess.run(
            ['ps', '-o', f'{field}=', '-p', str(pid)],
            stdout=subprocess.PIPE,
        )
        usage = int(res.stdout.decode().strip())
        if field == 'rss':
            return usage
        elif field == 'sz':
            return usage * page_size
        else:
            return ValueError(f'Unexpected field {field}')
    else:
        raise NotImplementedError('Unsupported platform')

def execute_command(
    command: List[str],
    memory_field: MemoryFieldsType,
    mem_get_sleep: float,
) -> List[float]:
    # execute command
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid = p.pid

    # get the memory usage history of the command
    memory_usages = []
    while p.poll() is None:
        usage_kb = exec_ps(pid, memory_field)
        usage_mb = usage_kb / 1024
        memory_usages.append(usage_mb) 
        time.sleep(mem_get_sleep)

    return memory_usages

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmarking Script")

    parser.add_argument(
        'memory-field',
        type=str, 
        choices=MemoryFields, 
        help='ps command field to retrieve memory usage',
    )
    parser.add_argument(
        'protocol',
        type=str, 
        choices=Protocols, 
        help='MPC protocol")',
    )
    parser.add_argument(
        'mem-get-sleep',
        type=float, 
        default=0.1,
        help='Time interval (in seconds) to sleep between memory retrievals'
    )
    parser.add_argument(
        'computation',
        type=argparse.FileType('r'),
        help='pyhton module that contains a computation',
    )
    parser.add_argument(
        'dataset',
        type=argparse.FileType('r'),
        help='dataset csv file',
    )
    parser.add_argument('--num-parties', type=int, default=3, help='Number of participating parties')

    return parser.parse_args()

args = parse_args()

print(f'args = {args}')

# Inputs:
# - MPC protocol: semi/mascot/etc
# - Number of parties: 3
# - Number of rows/ dataset
# - Computation


# - **Get measurements**:
#     - DONE: Compile time: time consumed by running `compile.py`
#     - RAM required when compiling (usually linear to circuit size):
#         - Could be estimated with [MP-SPDZ memory usage utility](https://mp-spdz.readthedocs.io/en/latest/utils.html#memory-usage)
#         - To measure real RAM usage, query the system, possibly with `ps`
#         - Try with complex computation
#     - Run time: fetched from MP-SPDZ output
#         
#         ```bash
#         Time = 0.02719 seconds
#         
#         ```
#         
#     - Communications: fetched from MP-SPDZ output
#         
#         ```bash
#         Data sent = 0.1252 MB in ~57 rounds (party 0 only; use '-v' for more details)
#         Global data sent = 0.254496 MB (all parties)
#         
#         ```
#         
#     - DONE: Bytecode size: bytecode is located under `Programs/Bytecode/`, e.g., get the size by `ls -l Programs/Bytecode/bmi-0.bc` for `bmi.mpc`
#         - it’s not necessarily circuit size but should be measured
# - output: `{’runtime’: xxx, ‘rounds’: xxx, }`
#     - check output is correct with testing lib
