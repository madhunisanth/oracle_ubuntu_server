#!/usr/bin/env python3
"""Conservative per-user Ubuntu cache cleanup. Standard library only."""
from pathlib import Path
import argparse
import logging
import os
import shutil
import stat
import time

HOME = Path.home()
TARGETS = ((HOME / '.cache' / 'thumbnails', 30), (HOME / '.cache' / 'ubuntu-gc-temp', 1))
LOG = HOME / '.local' / 'state' / 'ubuntu-gc' / 'cleanup.log'

def cleanup(dry_run=False):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=LOG, level=logging.INFO, format='%(asctime)s %(message)s')
    now = time.time()
    deleted = 0
    for root, age_days in TARGETS:
        if root.is_symlink() or not root.is_dir():
            continue
        for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
            for name in files:
                path = Path(base) / name
                try:
                    info = path.lstat()
                    if not stat.S_ISREG(info.st_mode) or now - info.st_mtime < age_days * 86400:
                        continue
                    if dry_run:
                        print('WOULD DELETE', path)
                    else:
                        path.unlink()
                        print('DELETED', path)
                    deleted += 1
                except (OSError, PermissionError) as exc:
                    logging.warning('Skipped %s: %s', path, exc)
    usage = shutil.disk_usage(HOME)
    summary = f'files={deleted} dry_run={dry_run} disk_used={usage.used / usage.total:.1%}'
    print(summary)
    logging.info(summary)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    cleanup(parser.parse_args().dry_run)
