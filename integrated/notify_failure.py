"""Notify the repository owner about failed sync attempts with bounded public diagnostics."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

HINTS = {
    'Plan exact upstream release': '上游版本或现有发布查询／版本规划失败。未开始发布。',
    'Test synchronization and preservation guards': '同步／OTA 保护测试失败，已阻止后续构建。',
    'Apply C11 source adaptation and reject credential files': '上游源码与 C11 补丁或功能／设置保护检查不兼容。',
    'All checks required by upstream AGENTS.md': '单元测试、lint 或调试构建未通过；不能把软件检查当作成功。',
    'Restore our own Android signing key': '固定签名资料恢复失败；没有改用新签名绕过。',
    'Build complete single APK': '正常源码 release APK 构建失败。',
    'Package matching source, guide and checksums': '包名、签名、Android 9、递增版本号或完整发布打包检查失败。',
    'Publish and verify the public OTA path': '发布或公开 OTA 检查失败；若已公开，会尝试撤回本次新包为草稿。',
}


def message(repo, run_id, attempt, jobs, details):
    owner = repo.split('/')[0]
    if not re.fullmatch(r'[A-Za-z0-9-]+', owner):
        raise ValueError('Invalid notification recipient')
    link = f'https://github.com/{repo}/actions/runs/{run_id}/attempts/{attempt}'
    title = f'[C11 自动更新失败] #{run_id} · 第 {attempt} 次执行'
    lines = [f'@{owner} 本次 C11 自动同步／更新失败。', '', f'执行记录：{link}', '', '失败步骤与说明：']
    for job in jobs:
        if job.get('conclusion') != 'failure': continue
        failed = [s for s in job.get('steps', []) if s.get('conclusion') == 'failure']
        for step in failed:
            name = step['name']
            lines.append(f'- **{name}**：{HINTS.get(name, "该步骤失败；详细日志见执行记录，暂不能据此判断根因。")}')
    if details.get('direct_reason'):
        reason = details['direct_reason'].replace('`', "'").replace('@', '＠')[:600]
        lines += ['', f'保护检查返回的直接原因：`{reason}`']
    tests = details.get('failed_tests', [])
    if tests:
        lines += ['', '失败测试（完整报告见该执行的附件）：']
        lines += [f'- `{test["test"]}`：`{test["error"]}`' for test in tests]
    lines += ['', '旧的可用发布不会被此流程删除或覆盖。请勿把未通过检查的新包当作可安装更新。',
              '以上为可确定的失败步骤／直接错误，最终根因可能仍需排查；这里不包含签名私钥或原始构建日志。']
    return title, '\n'.join(lines)+'\n'


def test_message(repo, run_id, attempt):
    _, body = message(repo, run_id, attempt,
        [dict(conclusion='failure', steps=[dict(name='Apply C11 source adaptation and reject credential files', conclusion='failure')])],
        dict(direct_reason='RuntimeError: [测试示例] 上游补丁锚点变化，已停止自动发布。'))
    body = body.replace('本次 C11 自动同步／更新失败。',
        '这是一条经你授权发送的通知链路测试。**没有发生真实同步失败，也没有改动 APK 或发布。**')
    body = body.replace('失败步骤与说明：', '以下仅演示未来失败通知的格式：')
    return f'[通知链路测试] C11 自动更新提醒 · #{run_id}', body


def send(repo, title, body):
    existing = json.loads(subprocess.check_output(['gh', 'issue', 'list', '--repo', repo, '--state', 'all',
                                                  '--search', f'"{title}" in:title', '--json', 'number,title']))
    if any(issue['title'] == title for issue in existing):
        print('Failure notification already exists for this attempt'); return
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / 'notification.md'; file.write_text(body)
        subprocess.run(['gh', 'issue', 'create', '--repo', repo, '--title', title, '--body-file', str(file)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-notification', action='store_true')
    args = parser.parse_args()
    repo = os.environ['GH_REPO']; run_id = int(os.environ['GITHUB_RUN_ID']); attempt = int(os.environ['GITHUB_RUN_ATTEMPT'])
    if args.test_notification:
        title, body = test_message(repo, run_id, attempt)
    else:
        jobs = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/actions/runs/{run_id}/jobs?filter=latest&per_page=100']))['jobs']
        reports = list(Path('failure').glob('**/c11-failure.json'))
        details = json.loads(reports[0].read_text()) if reports else {}
        title, body = message(repo, run_id, attempt, jobs, details)
    send(repo, title, body)


if __name__ == '__main__': main()
