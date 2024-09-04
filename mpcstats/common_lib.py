from pathlib import Path
repo_root = Path(__file__).parent.parent
mpcstats_dir = repo_root / 'mpcstats'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from Compiler.compilerLib import Compiler
from Compiler.types import sfix
from Compiler.library import print_ln
import subprocess
import config
import os
from typing import Callable, Any, Literal

# TODO generate list from type definition
ProtocolsType = Literal['semi', 'mascot']
Protocols = ['semi', 'mascot']

def compile_computation(
    name: str,
    computation: Callable[[], None],
    cfg: Any = config.DefaultMPSPDZSetting(),
) -> None:
    '''
    Compiles computation function and generates:
    - ./Programs/Schedules/{name}.sch
    - ./Programs/Bytecode/{name}-0.bc
    in the current directory
    '''
    def init_and_compute():
        sfix.round_nearest = cfg.round_nearest
        sfix.set_precision(cfg.f, cfg.k)
        computation()

    compiler = Compiler()
    compiler.register_function(name)(init_and_compute)

    # temporarily clear the command line arguments passed to the caller script
    # while executing compiler.compile_func
    # since it affects how compile.compile_func works
    bak = sys.argv
    sys.argv = [sys.argv[0]]
    compiler.compile_func()
    sys.argv = bak

def execute_computation(
    num_parties: int,
    mpc_script: str,
    name: str,
) -> str:
    cmd = f'PLAYERS={num_parties} {mpc_script} {name}'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        return res.stdout

    except subprocess.CalledProcessError as e:
        raise Exception(f'Executing MPC failed ({e.returncode}): stdout: {e.stdout}, stderr: {e.stderr}')

def execute_silently(f: Callable[[], None]) -> Any:
    stdout_bak = sys.stdout

    # redirect stdout to /dev/null
    sys.stdout = open(os.devnull, 'w')

    try:
        return f()
    finally:
        sys.stdout.close()
        sys.stdout = stdout_bak

def write_result(value: Any) -> None:
    print_ln('Result: %s', value)
