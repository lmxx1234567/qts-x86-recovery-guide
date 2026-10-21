#!/usr/bin/env python3
"""Prepare a local family-change candidate while preserving early boot mappings.
Optionally disable the exact known late-mod startup line; never touches a device.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from build_mod_overlay import unpack
from pack_overlay import regular, newc
from select_model import select

HOOK = b'/bin/busybox sh /qts-profile/mods/start > /tmp/qts-mods-start.log 2>&1 &\n'

def prepare(base, track, disable=False):
    entries = unpack(base)
    old = {n: d for n, d, mode in entries}
    init = old['sbin/init']
    if init.count(b'exec /bin/busybox init') != 1:
        raise ValueError('Unknown early-init handoff; review manually')
    model = select(old['qts-profile/model.conf'], track)
    removed = False
    if b'/qts-profile/mods/start' in init:
        if not disable:
            raise ValueError('Existing optional mods: validate them or explicitly disable the known hook')
        if init.count(HOOK) != 1 or init.count(b'/qts-profile/mods/start') != 1:
            raise ValueError('Unknown optional startup hook; not removed')
        init = init.replace(HOOK, b'')
        removed = True
    replacements = {'sbin/init': init, 'qts-profile/model.conf': model}
    updated = [(n, replacements.get(n, d), mode) for n, d, mode in entries]
    blob = gzip.compress(b''.join(newc(n, d, mode, i+1)
        for i, (n, d, mode) in enumerate(updated + [('TRAILER!!!', b'', 0)])), mtime=0)
    return blob, {'base_sha256': hashlib.sha256(base).hexdigest(),
        'sha256': hashlib.sha256(blob).hexdigest(), 'model_track': track,
        'known_optional_startup_disabled': removed,
        'early_init_change': 'remove exact late-mod hook only' if removed else 'none',
        'other_members_unchanged': True,
        'warning': 'Review any other helpers and diagnostic module paths separately; no runtime compatibility claim'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True, type=Path)
    p.add_argument('--track', required=True, choices=['x77', 'x73a'])
    p.add_argument('--disable-optional-mods', action='store_true')
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    blob, report = prepare(regular(a.base), a.track, a.disable_optional_mods)
    with a.output.open('xb') as f:
        f.write(blob)
    a.output.with_suffix('.review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
