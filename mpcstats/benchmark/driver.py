#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'
computation_def_dir = benchmark_dir / 'computation_defs'

import subprocess
import json
from protocols import all_protocols

headers = [
    ('computation', 'm'),
    ('protocol', 'e'),
    ('category', 'm'),
    ('rounds', 'e'),
    ('compilation_time', 'c'),
    ('time_sec', 'e'),
    ('compile_max_mem_usage_kb', 'c'),
    ('executor_max_mem_usage_kb', 'e'),
    ('total_bytecode_size', 'c'),
    #('executor_exec_time_sec', 'e'),
    #('compile_exec_time_sec', 'c'),
    ('statistical security parameter', 'e'),
    ('data_sent_by_party_0', 'e'),
    ('global_data_sent_mb', 'e'),
    ('result', 'e'),
]

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
        if comp != {} and typ == 'c':
            col = str(comp[key])
        elif exe != {} and typ == 'e':
            col = str(exe[key])
        elif meta != {} and typ == 'm':
            col = str(meta[key])
        cols.append(col)

    return ','.join(cols)

def write_benchmark_result(computation_def: Path, protocol: str, program: str, category: str) -> None:
    cmd = [benchmark_dir / 'benchmarker.py', protocol, '--file', computation_def]
    result = subprocess.run(cmd, capture_output=True, text=True)
    result_obj = json.loads(result.stdout)
    result_obj.append({
        'computation': computation_def.stem,
        'category': category,
    })
    print(gen_line(result_obj))

subprocess.run([benchmark_dir / 'gen_comp_defs.py'], check=True)

# print header
print(gen_header())

# List all files in the directory
computation_defs = [file for file in computation_def_dir.iterdir() if file.is_file()]

# print benchmark result rows
for computation_def in computation_defs:
    for protocol, program, category in all_protocols:
        if protocol != '':
            write_benchmark_result(computation_def, protocol, program, category)

