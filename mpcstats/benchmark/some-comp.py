from pathlib import Path
repo_root = Path(__file__).parent.parent

import sys
sys.path.append(str(repo_root))

from Compiler.library import print_ln

def computation():
    print_ln('hello')

