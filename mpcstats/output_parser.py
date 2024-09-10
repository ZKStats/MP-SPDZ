import json
import re
from typing import Any

def parser(attrs: object, line: str, key: str, regex: str) -> bool:
    m = re.match(regex, line)
    if m is None:
        return False
    attrs[key] = m.group(1)
    return True

def parse_execution_output(output: str) -> object:
    attrs = {}

    for line in output.split('\n'):
        parser(attrs, line, 'Result', r'^Result: (.*)$') or \
        parser(attrs, line, 'Statistical Security Parameter', r'^Using statistical security parameter (.*)$') or \
        parser(attrs, line, 'Time (sec)', r'^Time = (.*) seconds.*$') or \
        parser(attrs, line, 'Data sent (party 0 only)', r'^Data sent = (.*) \(.*$') or \
        parser(attrs, line, 'Global data sent (all parties; MB)', r'^Global data sent = (.*) MB.*$') or \
        parser(attrs, line, 'Global data sent (all parties; MB)', r'^Global data sent = (.*) MB.*$')

    return attrs

def parse_compiler_output(output: str) -> object:
    attrs = {}

    for line in output.split('\n'):
        parser(attrs, line, 'Virtual machine rounds', r'^ +\d*) [^ ]+$') or \
        True

    return attrs
