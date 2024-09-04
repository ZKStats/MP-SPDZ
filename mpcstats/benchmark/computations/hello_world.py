from pathlib import Path
repo_root = Path(__file__).parent.parent.parent

import sys
sys.path.append(str(repo_root))
sys.path.append(f'{repo_root}/mpcstats')

from Compiler.library import print_ln
from common_lib import write_result

def computation():
    write_result('hello')

