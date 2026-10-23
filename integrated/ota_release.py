"""Publish complete assets, then verify the actual unauthenticated OTA path."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.request
from release_plan import complete

TAG = re.compile(r'c11-v(\d+)\.(\d+)\.(\d+)-c11\.(\d+)')


def version_key(tag):
    match = TAG.fullmatch(tag)
    return tuple(map(int, match.groups())) if match else None


def validate_catalog(releases, expected):
    candidates = []
    for release in releases:
        key = version_key(release.get('tag_name', ''))
        if key and complete(release, '.'.join(map(str, key[:3])), key[3]):
            candidates.append((key, release))
    if not candidates or max(candidates, key=lambda x: x[0])[1]['tag_name'] != expected:
        raise ValueError('公开 OTA 列表按数字选择的最新完整版本不是本次版本')
    # c11.9 only reads entry zero; newer clients scan the numerical maximum.
    if not releases or releases[0].get('tag_name') != expected:
        raise ValueError('c11.9 更新接口首条不是本次版本，旧客户端无法发现它')
    return next(release for _, release in candidates if release['tag_name'] == expected)


def request(url):
    return urllib.request.Request(url, headers={
        'User-Agent': 'DiPlay/0.2.21-c11.9', 'Accept': 'application/vnd.github+json'})


def verify_public(repo, expected, apk_name, digest):
    api = f'https://api.github.com/repos/{repo}/releases?per_page=30'
    with urllib.request.urlopen(request(api), timeout=45) as response:
        releases = json.load(response)
    release = validate_catalog(releases, expected)
    assets = {a['name']: a for a in release['assets']}
    prefix = f'https://github.com/{repo}/releases/download/{expected}/'
    for name in [apk_name, 'SHA256SUMS.txt']:
        if not assets.get(name, {}).get('browser_download_url', '').startswith(prefix):
            raise ValueError(f'OTA 文件地址不属于本次发布：{name}')
    with urllib.request.urlopen(request(assets['SHA256SUMS.txt']['browser_download_url']), timeout=45) as response:
        sums = response.read(65537)
    if len(sums) > 65536:
        raise ValueError('OTA 校验文件过大')
    entries = dict((parts[1].lstrip('*'), parts[0]) for line in sums.decode().splitlines()
                   if len(parts := line.split()) == 2)
    if entries.get(apk_name) != digest:
        raise ValueError('公开 OTA 校验文件与已验证 APK 不一致')
    actual = hashlib.sha256()
    with urllib.request.urlopen(request(assets[apk_name]['browser_download_url']), timeout=60) as response:
        while chunk := response.read(1024 * 1024):
            actual.update(chunk)
    if actual.hexdigest() != digest:
        raise ValueError('从公开 OTA 下载的 APK 校验失败')
    return dict(tag=expected, numeric_latest=True, c11_9_first=True, public_apk_sha256=digest)


def publish(repo, tag, folder):
    apk = list(folder.glob('*.apk'))
    if len(apk) != 1:
        raise ValueError('发布目录必须有一个完整 APK')
    digest = hashlib.sha256(apk[0].read_bytes()).hexdigest()
    # A draft with this tag is never overwritten; release_plan already rejects partial tags.
    subprocess.run(['gh', 'release', 'create', tag, '--repo', repo, '--target', os.environ['GITHUB_SHA'],
                    '--draft', '--prerelease', '--title', f'DiPlay C11 一体测试版 · {tag}',
                    '--notes-file', 'integrated/说明.md'] + [str(p) for p in sorted(folder.iterdir()) if p.is_file()], check=True)
    promoted = False
    try:
        promoted = True
        subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--draft=false'], check=True)
        last = None
        for attempt in range(3):
            try:
                result = verify_public(repo, tag, apk[0].name, digest)
                summary = os.environ.get('GITHUB_STEP_SUMMARY')
                if summary:
                    with open(summary, 'a') as out:
                        out.write(f'\n## OTA 核验通过\n\n`{tag}`：数字版本选择、c11.9 首条、公开 APK 下载及 SHA256 一致。\n')
                return result
            except Exception as error:
                last = error
                if attempt < 2:
                    time.sleep(10)
        raise ValueError(f'发布后 OTA 核验失败：{last}')
    except Exception:
        if promoted:
            # Quarantine only the new release, never touch an older working release.
            try:
                subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--draft=true'], check=True)
            except subprocess.CalledProcessError as rollback:
                raise RuntimeError('OTA 核验或发布失败，且撤回草稿失败；请立即检查本次发布状态') from rollback
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-existing', action='store_true')
    args = parser.parse_args()
    if args.verify_existing:
        apk = next(Path('dist/r104-release').glob('*.apk'))
        print(json.dumps(verify_public(os.environ['GH_REPO'], 'c11-v0.2.21-c11.104', apk.name,
                                      hashlib.sha256(apk.read_bytes()).hexdigest()), indent=2))
    else:
        print(json.dumps(publish(os.environ['GH_REPO'], os.environ['C11_TAG'], Path('integrated-release')), indent=2))
