"""Plan an additive C11 build; never overwrite a release or downgrade the catalog."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync_upstream import select_release, list_releases


def complete(release, version, revision):
    names = {a['name'] for a in release.get('assets', [])}
    return not release.get('draft') and {
        f'DiPlay-C11-{version}-c11.{revision}.apk', 'DiPlay-C11-source.zip',
        'C11-Integrated-Guide-ZH.md', 'SHA256SUMS.txt', 'upstream.json',
    }.issubset(names)


def make_plan(config, upstream_releases, own_releases):
    if config['upstream'] != 'shihabal3amri/DiPlay':
        raise ValueError('Unexpected upstream repository')
    revision = config['revision']
    if type(revision) is not int or not 1 <= revision <= 999:
        raise ValueError('Invalid C11 revision')
    release, _ = select_release(upstream_releases)
    version = release['tag_name'][1:]
    tag = f'c11-v{version}-c11.{revision}'
    key = (*map(int, version.split('.')), revision)
    for own in own_releases:
        if own['tag_name'] == tag:
            if not complete(own, version, revision):
                raise ValueError(f'{tag} exists but is incomplete/draft; refusing to overwrite it')
            return dict(needed='false', tag=tag, upstream_tag=release['tag_name'], version=version,
                        revision=revision, reason='already published')
        match = re.fullmatch(r'c11-v(\d+\.\d+\.\d+)-c11\.(\d+)', own['tag_name'])
        if match and complete(own, match[1], match[2]):
            if (*map(int, match[1].split('.')), int(match[2])) > key:
                return dict(needed='false', tag=tag, upstream_tag=release['tag_name'], version=version,
                            revision=revision, reason='newer C11 release already published')
    return dict(needed='true', tag=tag, upstream_tag=release['tag_name'], version=version,
                revision=revision, reason='new upstream release or adaptation revision')


def main():
    config = json.loads(Path('integrated/config.json').read_text())
    plan = make_plan(config, list_releases(config['upstream']), list_releases(os.environ['GH_REPO']))
    if plan['needed'] == 'true':
        commit = json.loads(subprocess.check_output([
            'gh', 'api', f'repos/{config["upstream"]}/commits/{plan["upstream_tag"]}']))
        sha = commit['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Invalid upstream commit SHA')
        plan['upstream_sha'] = sha
    else:
        plan['upstream_sha'] = ''
    with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
        for key, value in plan.items():
            out.write(f'{key}={value}\n')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as out:
            out.write(f'## C11 upstream synchronization\n\nUpstream: `{plan["upstream_tag"]}`\n\n'
                      f'C11 release: `{plan["tag"]}`\n\nDecision: {plan["reason"]}\n')
    print('C11 integrated plan:', plan['tag'], 'needed=' + plan['needed'], plan['reason'])


if __name__ == '__main__':
    main()
