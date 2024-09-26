#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'
computation_def_dir = benchmark_dir / 'computation_defs'
templates_dir = benchmark_dir / 'computation_defs' / 'templates'
scripts_dir = repo_root / 'Scripts'
datasets_dir = benchmark_dir / 'datasets'

import argparse
import subprocess
import json
from typing import Any
from protocols import all_protocols
from constants import COMPUTATION, PROTOCOL, CATEGORY, ROUNDS, COMPILATION_TIME, EXECUTION_TIME, COMPILE_MAX_MEM_USAGE_KB, EXECUTOR_MAX_MEM_USAGE_KB, TOTAL_BYTECODE_SIZE, EXECUTOR_EXEC_TIME_SEC, COMPILE_EXEC_TIME_SEC, STATISTICAL_SECURITY_PARAMETER, DATA_SENT_BY_PARTY_0, GLOBAL_DATA_SENT_MB, RESULT

COMP='comp'
EXEC='exec'
META='meta'

headers = [
    (COMPUTATION, META),
    (PROTOCOL, META),
    (CATEGORY, META),
    (ROUNDS, EXEC),
    (COMPILATION_TIME, COMP),
    (EXECUTION_TIME, EXEC),
    (COMPILE_MAX_MEM_USAGE_KB, COMP),
    (EXECUTOR_MAX_MEM_USAGE_KB, EXEC),
    (TOTAL_BYTECODE_SIZE, COMP),
    #(EXECUTOR_EXEC_TIME_SEC, EXEC),
    #(COMPILE_EXEC_TIME_SEC, COMP),
    (STATISTICAL_SECURITY_PARAMETER, EXEC),
    (DATA_SENT_BY_PARTY_0, EXEC),
    (GLOBAL_DATA_SENT_MB, EXEC),
    (RESULT, EXEC),
]

scenarios = [
    ['all'],
    ['test'],
    ['mean'],
    ['where'],
    ['join'],
]

def scenario_desc() -> str:
    lines = []
    for id, names in enumerate(scenarios):
        names_str = ','.join(names)
        lines.append(f'{id}: {names_str}')

    return ' '.join(lines)

def parse_args() -> Any:
    parser = argparse.ArgumentParser(description='Benchmarking driver')
    parser.add_argument(
        'id',
        type=int,
        help=f'Scenario id: {scenario_desc()}',
    )
    parser.add_argument(
        'dataset', 
        type=int, 
        choices=[100, 1000, 10000, 100000], 
        help='Dataset to use. 100, 1000, 10000 or 100000',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show output from Comipler module',
    )
    return parser.parse_args()

def activate_all(dir: Path) -> None:
    for file in dir.iterdir():
        if file.name.startswith('_'):
            new_name = file.with_name(file.name[1:])
            file.rename(dir / new_name)

def deactivate_all(dir: Path) -> None:
    for file in dir.iterdir():
        if not file.name.startswith('_'):
            new_name = file.with_name(f'_{file.name}')
            file.rename(dir / new_name)

def activate(dir: Path, name: str, ext: str) -> None:
    file = dir / f'_{name}.{ext}'
    file.rename(dir / f'{name}.{ext}')

def gen_header() -> str:
    return ','.join([header[0] for header in headers])

def gen_line(result: object) -> str:
    comp = result[0] # compilation stats
    exe = result[1] # execution stats
    meta = result[2] # meta data

    cols = []
    for header in headers:
        key = header[0]
        typ = header[1]

        col = ''
        if comp != {} and typ == COMP:
            col = str(comp[key])
        elif exe != {} and typ == EXEC:
            col = str(exe[key])
        elif meta != {} and typ == META:
            col = str(meta[key])
        cols.append(col)

    return ','.join(cols)

def write_benchmark_result(
    computation_def: Path,
    protocol: str,
    comp_args: str,
    category: str,
    args: Any) -> None:

    cmd = [benchmark_dir / 'benchmarker.py', protocol, '--file', computation_def, '--comp-args', comp_args]
    if args.verbose:
        cmd.append('--verbose')

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        result_obj = json.loads(result.stdout)
    except:
        print(str(result).replace('\\n', '\n'))
        raise
    result_obj.append({
        'computation': computation_def.stem,
        'category': category,
        'protocol': protocol,
    })
    print(gen_line(result_obj))

args = parse_args()

# set up scenario
if args.id == 0:
    activate_all(templates_dir)

elif args.id > 0:
    deactivate_all(templates_dir)
    names = scenarios[args.id]
    for name in names:
        activate(templates_dir, name, 'py')
        print(f'Activated {name} scenario')

# activate targetted dataset
deactivate_all(datasets_dir)
activate(datasets_dir, f'10x{args.dataset}', 'csv')

# generate required VMs
subprocess.run([benchmark_dir / 'gen_vms.py'], check=True)

# generate computation defs from the tempaltes
subprocess.run([benchmark_dir / 'gen_comp_defs.py'], check=True)

# print header
print(gen_header())

# List all files in the directory
computation_defs = [file for file in computation_def_dir.iterdir() if file.is_file()]

# validate protocols
for protocol, _, comp_args, category in all_protocols:
    if protocol.endswith('.sh'):
        print(f'Drop .sh from {protocol}')
        exit(0)

# print benchmark result rows
for computation_def in computation_defs:
    for protocol, _, comp_args, category in all_protocols:
        if protocol != '':
            write_benchmark_result(
                computation_def,
                protocol,
                comp_args,
                category,
                args)

