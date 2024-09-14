import json
import re
from typing import Any

def parser(attrs: object, line: str, keys: list[str], regex: str) -> bool:
    m = re.match(regex, line)
    if m is None:
        return False
    for i in range(len(keys)):
        attrs[keys[i]] = m.group(i + 1)
    return True

def parse_execution_output(output: str) -> object:
    attrs = {}

    for line in output.split('\n'):
        parser(attrs, line, ['result'], r'^Result: (.*)$') or \
        parser(attrs, line, ['statistical security parameter'], r'^Using statistical security parameter (.*)$') or \
        parser(attrs, line, ['time_sec'], r'^Time = (.*) seconds.*$') or \
        parser(attrs, line, ['data_sent_by_party_0', 'rounds'], r'^Data sent = ([^\s]+) MB [^~]*~([^s]+) rounds.*$') or \
        parser(attrs, line, ['global_data_sent_mb'], r'^Global data sent = (.*) MB.*$') or \
        True

    return attrs

def parse_compiler_output(output: str) -> object:
    attrs = {}

    for line in output.split('\n'):
        parser(attrs, line, ['Virtual machine rounds'], r'^ +\d*) [^ ]+$') or \
        True

    return attrs
