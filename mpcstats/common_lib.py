from pathlib import Path
repo_root = Path(__file__).parent.parent
mpcstats_dir = repo_root / 'mpcstats'

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from Compiler.compilerLib import Compiler
from Compiler.types import sfix
import config

def compile_computation(
    name,
    computation,
    cfg = config.DefaultMPSPDZSetting(),
):
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

