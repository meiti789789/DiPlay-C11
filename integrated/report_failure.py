"""Export names/types of failed tests and trusted guard errors, not raw logs or credentials."""
import html
import json
import os
from pathlib import Path
import re


def report(root, direct):
    failures = []
    for path in root.glob('**/build/reports/tests/**/*.html'):
        text = path.read_text(errors='replace')
        for method, body in re.findall(r'<pre[^>]*id="[^"]*test-failure-([^"]+)"[^>]*>(.*?)</pre>', text, re.S):
            exception = re.search(r'([\w.]+(?:Error|Exception))', html.unescape(body))
            name = re.sub(r'[^\w.$()\[\] -]', '', html.unescape(method))[:180]
            failures.append(dict(test=name, error=exception[1] if exception else '断言或测试错误'))
    return dict(direct_reason=json.loads(direct.read_text()).get('reason') if direct.is_file() else None,
                failed_tests=failures[:30])


if __name__ == '__main__':
    data = report(Path('upstream'), Path(os.environ['RUNNER_TEMP']) / 'c11-direct-error.json')
    Path('c11-failure.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
