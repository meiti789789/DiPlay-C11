"""Mirror unmodified upstream releases. No vehicle access; no compatibility claim."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

UPSTREAM = 'shihabal3amri/DiPlay'

def api(path):
    raw = subprocess.check_output(['gh', 'api', path])
    return json.loads(raw)

def select_release(releases):
    for release in releases:
        if release.get('draft'):
            continue
        tag = release.get('tag_name', '')
        if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
            continue
        version = tag[1:]
        assets = {asset['name']: asset for asset in release.get('assets', [])}
        names = [f'DiPlay-{version}.apk', f'DiPlay-{version}-source.zip']
        if all(name in assets for name in names):
            chosen = [assets[name] for name in names]
            for asset in chosen:
                if not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
                    raise ValueError('Upstream asset lacks a SHA256 digest; refusing unchecked mirror')
            return release, chosen
    raise ValueError('No supported upstream release with matching APK and source')

def verify(path, digest):
    actual = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        raise ValueError(f'Integrity mismatch: {path.name}')

def main():
    own = os.environ['GH_REPO']
    release, assets = select_release(api(f'repos/{UPSTREAM}/releases?per_page=10'))
    version = json.loads(Path('version.json').read_text())['name']
    tag = f'c11-upstream-{release["tag_name"]}-bridge-{version}'
    # Listing avoids confusing authentication/server errors with a missing release.
    existing = api(f'repos/{own}/releases?per_page=100')
    if any(r['tag_name'] == tag for r in existing):
        print('Already synchronized:', tag)
        return
    bridge_tag = 'bridge-v' + version
    bridge = api(f'repos/{own}/releases/tags/{bridge_tag}')
    apk_name = f'C11-WheelBridge-{version}.apk'
    bridge_assets = [a for a in bridge['assets'] if a['name'] == apk_name]
    if len(bridge_assets) != 1:
        raise ValueError('Signed companion release must exist before upstream synchronization')
    bridge_digest = bridge_assets[0].get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', bridge_digest):
        raise ValueError('Companion asset has no SHA256 digest')
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)
        # Download via gh using exact asset names; never execute upstream source or release notes.
        for asset in assets:
            subprocess.run(['gh', 'release', 'download', release['tag_name'], '--repo', UPSTREAM,
                            '--pattern', asset['name'], '--dir', str(out)], check=True)
            verify(out / asset['name'], asset['digest'])
        subprocess.run(['gh', 'release', 'download', bridge_tag, '--repo', own,
                        '--pattern', apk_name, '--pattern', 'C11-WheelBridge-source.zip',
                        '--dir', str(out)], check=True)
        verify(out / apk_name, bridge_digest)
        # Validate the companion source archive as well.
        source = next(a for a in bridge['assets'] if a['name'] == 'C11-WheelBridge-source.zip')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', source.get('digest') or ''):
            raise ValueError('Companion source has no digest')
        verify(out / source['name'], source['digest'])
        manifest = {
            'upstream': UPSTREAM, 'upstream_tag': release['tag_name'],
            'upstream_url': release['html_url'], 'bridge_version': version,
            'compatibility': 'UNVERIFIED on 2023 C11; automatic synchronization is not vehicle validation',
            'upstream_apk_modified': False,
            'assets': {a['name']: a['digest'] for a in assets + [bridge_assets[0], source]},
        }
        (out / 'upstream.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        (out / 'SHA256SUMS.txt').write_text(''.join(
            hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n'
            for p in sorted(out.iterdir()) if p.is_file()))
        notes = out / 'RELEASE_NOTES.md'
        notes.write_text(f'''自动同步上游 {release['tag_name']} + C11 方控桥接 {version}。

**待实车验证。自动同步不代表此版本已在 2023 C11 增程验证通过。**

- `DiPlay-*.apk` 是上游原始 APK，未修改、未重签；原版 DiPlay 保留自己的在线升级机制。
- `C11-WheelBridge-*.apk` 是独立桥接应用，需要手动通知使用权，首次转发默认关闭。
- 当前零跑分支与上游原版签名不同，不能保证直接覆盖安装；请勿先卸载工作正常的版本。
- 两套方控同时生效时关闭桥接，避免重复切歌。
- 不刷车机、不写 CAN、不执行 ADB。实车所有 ADB 操作须由车主单独批准。
- 上游来源：{release['html_url']} ，完整对应源码附在发布附件中。
- 方控协议参考：https://github.com/Wh1t3co1azZ/DiPlay-Leapmotor
- GPL-3.0 声明与其它上游许可见源码仓库。保留原作者版权，无官方合作或认证关系。

这里的自动更新是仓库定时同步新发布，并非车机静默安装；未来接口变化仍可能需要更新桥接。

详细安装、授权、按键测试与故障排查：[使用说明](https://github.com/{own}/blob/main/使用说明.md)。
''')
        subprocess.run(['gh', 'release', 'create', tag, '--repo', own, '--target', 'main',
                        '--prerelease', '--title', f'C11 组合测试包 · {release["tag_name"]} + 桥接 {version}',
                        '--notes-file', str(notes)] + [str(p) for p in sorted(out.iterdir()) if p != notes], check=True)

if __name__ == '__main__':
    main()
