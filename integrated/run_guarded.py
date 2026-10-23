"""Preserve the direct error from public adaptation/OTA scripts, never private signing commands."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    result = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout, end='')
    print(result.stderr, file=sys.stderr, end='')
    if result.returncode:
        # Only known public guard exceptions are copied into a notification, never general logs.
        lines = [line for line in result.stderr.splitlines() if line.startswith(('ValueError:', 'RuntimeError:'))]
        reason = lines[-1][:600] if lines else '该步骤命令失败；详细原因见对应步骤日志。'
        Path(os.environ['RUNNER_TEMP'], 'c11-direct-error.json').write_text(json.dumps({'reason': reason}))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
