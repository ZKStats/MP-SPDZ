#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
mpcstats_dir = repo_root / 'mpcstats'
benchmark_dir = mpcstats_dir / 'benchmark'
templates_dir = benchmark_dir / 'computation_defs' / 'templates'

import argparse
from typing import Any
import subprocess

scenarios = [
    ['all'],
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
    parser = argparse.ArgumentParser(description='Scenario setup script')
    parser.add_argument(
        'id',
        type=int,
        help=f'Scenario id: {scenario_desc()}',
    )
    return parser.parse_args()

args = parse_args()

def activate_all() -> None:
    for file in templates_dir.iterdir():
        if file.name.startswith('_'):
            new_name = file.with_name(file.name[1:])
            file.rename(templates_dir / new_name)

def deactivate_all() -> None:
    for file in templates_dir.iterdir():
        if not file.name.startswith('_'):
            new_name = file.with_name(f'_{file.name}')
            file.rename(templates_dir / new_name)

def activate(name: str) -> None:
    file = templates_dir / f'_{name}.py'
    file.rename(templates_dir / f'{name}.py')

if args.id == 0:
    activate_all()

elif args.id > 0:
    deactivate_all()
    names = scenarios[args.id]
    for name in names:
        activate(name)
        print(f'Activated {name}.py')

subprocess.run([benchmark_dir / 'gen_comp_defs.py'])
