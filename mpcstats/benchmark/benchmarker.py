#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

import argparse
import subprocess
import os
import time
from typing import List, Literal
import json
from common_lib import Protocols, ProtocolsType, read_script 

# TODO generate list from type definition
MemoryFieldsType = Literal['sz', 'rss']
MemoryFields = ['sz', 'rss']

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
        'protocol',
        type=str, 
        choices=Protocols, 
        help='MPC protocol',
    )
    parser.add_argument(
        'dataset',
        type=argparse.FileType('r'),
        help='dataset csv file',
    )
    parser.add_argument(
        '--name',
        type=str,
        default=f'computation',
        help='Name of the computation',
    )
    parser.add_argument(
        '--memory-field',
        type=str, 
        choices=MemoryFields,
        default='sz',
        help='ps command field to retrieve memory usage',
    )
    parser.add_argument(
        '--edabit',
        action='store_true',
        help='Use edaBit',
    )
    parser.add_argument(
        '--mem-get-sleep',
        type=float, 
        default=0.1,
        help='Time interval (in seconds) to sleep between memory retrievals'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Computation definition file. If not specified, the definition will be read from stdin',
    )
    parser.add_argument('--num-parties', type=int, default=3, help='Number of participating parties')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show output from internally called scripts',
    )
    return parser.parse_args()

args = parse_args()

def gen_compile_cmd(args: list[str]) -> list[str]:
    compile_script = benchmark_dir / 'compile.py'
    opts = []
    if args.name:
        opts.extend(['--name', args.name])
    if args.file:
        opts.extend(['--file', args.file])
    if args.edabit:
        opts.append('--edabit')
    if args.verbose:
        opts.append('--verbose')

    return [compile_script] + opts

def gen_executor_cmd(args: list[str]) -> list[str]:
    executor_script = benchmark_dir / 'executor.py'
    opts = []
    if args.name:
        opts.extend(['--name', args.name])
    if args.file:
        opts.extend(['--file', args.file])
    if args.verbose:
        opts.append('--verbose')
 
    return [executor_script, args.protocol] + opts

def exec_cmd(cmd, computation_script) -> object:
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _ = proc.communicate(input=computation_script.encode())
    lines = output.splitlines()

    # print out output script output except the last line in utf-8
    other_lines = [line.decode('utf-8') for line in lines[:-1]]
    print('\n'.join(other_lines))

    # return the last line as a json object
    return json.loads(lines[-1])

# read computaiton script from file or stdin
computation_script = read_script(args.file)

# execute compile script
compile_output = exec_cmd(gen_compile_cmd(args), computation_script)
print(compile_output)

# execute executor script
executor_output = exec_cmd(gen_executor_cmd(args), computation_script)
print(executor_output)

