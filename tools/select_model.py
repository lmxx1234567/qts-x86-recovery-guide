#!/usr/bin/env python3
"""Select reviewed X77/X73A identity fields in a local model file, never on a NAS.
This is not hardware discovery or a firmware compatibility check.
"""
import argparse
import configparser
import re
from pathlib import Path
from pack_overlay import regular

TRACKS = {
    'x77': {'MODEL': 'TS-877', 'CAP': '0x1414db1c'},
    'x73a': {'MODEL': 'TS-873A', 'DISPLAY_FIXED_MODEL_NAME': 'TS-873A',
             'CAP': '0x4149b1c', 'CAP_EXT': '0x00040000'},
}
KEYS = set().union(*[set(v) for v in TRACKS.values()])

def select(data, track):
    text = data.decode('utf-8')
    cfg = configparser.RawConfigParser(strict=True)
    cfg.optionxform = str
    cfg.read_string(text)
    current = dict(cfg.items('System Enclosure'))
    identity = {k: current[k] for k in KEYS if k in current}
    if identity not in TRACKS.values():
        raise ValueError('Unknown identity/capabilities: review the model instead of forcing it')
    for section in ('Boot Enclosure', 'Boot Disk 1'):
        if not cfg.has_section(section):
            raise ValueError('Missing protected boot section: ' + section)
    if not any(n.startswith('System Disk ') for n in cfg.sections()):
        raise ValueError('Missing data-bay mapping')
    if not any(n.startswith('System Network ') for n in cfg.sections()):
        raise ValueError('Missing network mapping')
    headers = list(re.finditer(r'^\[([^\]\r\n]+)\][ \t]*\r?$', text, re.M))
    matches = [(i, m) for i, m in enumerate(headers) if m.group(1) == 'System Enclosure']
    if len(matches) != 1:
        raise ValueError('Ambiguous System Enclosure header')
    i, header = matches[0]
    end = headers[i+1].start() if i+1 < len(headers) else len(text)
    section = text[header.end():end]
    section = ''.join(line for line in section.splitlines(True)
                      if not any(re.match(r'^\s*' + k + r'\s*=', line) for k in KEYS))
    newline = '\r\n' if '\r\n' in text else '\n'
    values = ''.join(k + ' = ' + v + newline for k, v in TRACKS[track].items())
    # Keep every other line and section byte-for-byte; only identity fields move.
    result = text[:header.end()] + newline + values + section.lstrip('\r\n') + text[end:]
    return result.encode('utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--track', choices=sorted(TRACKS), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = select(regular(args.input), args.track)
    with args.output.open('xb') as output:
        output.write(data)
    print('Selected', args.track, 'identity only; validate drivers and every HAL bay before storage startup.')

if __name__ == '__main__':
    main()
