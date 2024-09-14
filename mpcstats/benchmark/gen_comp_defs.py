#!/usr/bin/env python3

from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
benchmark_dir = repo_root / 'mpcstats' / 'benchmark'
datasets_dir = benchmark_dir / 'datasets'
computation_def_dir = benchmark_dir / 'computation_defs'
computation_def_tmpl_dir = computation_def_dir / 'templates'

def apply_line_filter(line: int, num_parties: int, dataset: Path) -> str:
    line = line.replace("'::NUM_PARTIES::'", str(num_parties))
    line = line.replace("'::DATASET_FILE::'", f"'{dataset.name}'")
    return line

def create_instance(template: Path, num_parties: int, dataset: Path) -> None:
    file_name = f'{template.stem}_{dataset.stem}_{num_parties}.py'
    instance = computation_def_dir / file_name
    with open(instance, 'w') as inst_file:
        with open(template) as tmpl_file:
            for line in tmpl_file:
                line = apply_line_filter(line, num_parties, dataset)
                inst_file.write(line)

num_parties_list = [2, 3]
datasets = [file for file in datasets_dir.iterdir()]
templates = [file for file in computation_def_tmpl_dir.iterdir()]

# delete all existing instance files
for x in computation_def_dir.iterdir():
    if x.is_file():
        x.unlink()

for dataset in datasets:
    if dataset.name.startswith('_'):
        continue
    for template in templates:
        if template.name.startswith('_'):
            continue
        for num_parties in num_parties_list:
            create_instance(template, num_parties, dataset)

