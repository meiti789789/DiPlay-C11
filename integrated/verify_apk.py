"""Check the produced APK before any automated release becomes visible."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from release_plan import complete
from sync_upstream import list_releases

SIGNER = 'd81eca4365d29a2519577fd08a41e138ff89da95840b90be25df1c0952a507af'
BASELINE_TAG = 'c11-v0.2.21-c11.104'
BASELINE_CODE = 40104


def inspect(badging, certificates, expected_version, previous_code):
    package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    sdk = re.search(r"^sdkVersion:'(\d+)'", badging, re.M)
    if not package or package[1] != 'com.c11.diplay':
        raise ValueError('APK package identity mismatch')
    if package[3] != expected_version:
        raise ValueError('APK version name mismatch')
    if int(package[2]) <= previous_code:
        raise ValueError('APK versionCode does not increase; OTA install would be rejected')
    if not sdk or int(sdk[1]) > 28:
        raise ValueError('APK no longer supports Android 9 / API 28')
    digests = re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', certificates)
    if digests != [SIGNER]:
        raise ValueError('APK must have exactly the existing C11 signer')
    return dict(package=package[1], version_code=int(package[2]), version_name=package[3],
                min_sdk=int(sdk[1]), signer_sha256=SIGNER)


def previous_version_code(repo):
    candidates = []
    for release in list_releases(repo):
        match = re.fullmatch(r'c11-v(\d+\.\d+\.\d+)-c11\.(\d+)', release['tag_name'])
        if match and complete(release, match[1], match[2]):
            candidates.append(((*map(int, match[1].split('.')), int(match[2])), release))
    if not candidates:
        raise ValueError('No previous complete C11 release; manual initialization required')
    previous = max(candidates, key=lambda entry: entry[0])[1]
    if previous['tag_name'] == BASELINE_TAG:
        return BASELINE_CODE
    if not any(a['name'] == 'c11-build.json' for a in previous['assets']):
        raise ValueError('Previous release lacks versionCode evidence; refusing unchecked OTA')
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(['gh', 'release', 'download', previous['tag_name'], '--repo', repo,
                        '--pattern', 'c11-build.json', '--dir', directory], check=True)
        code = json.loads((Path(directory) / 'c11-build.json').read_text())['version_code']
    if type(code) is not int or code < BASELINE_CODE:
        raise ValueError('Invalid previous versionCode evidence')
    return code


def main():
    apks = list(Path('integrated-release').glob('*.apk'))
    if len(apks) != 1:
        raise ValueError('Expected exactly one complete APK')
    tools = Path(os.environ['ANDROID_HOME']) / 'build-tools/36.0.0'
    certificates = subprocess.check_output([str(tools / 'apksigner'), 'verify', '--min-sdk-version',
                                           '28', '--verbose', '--print-certs', str(apks[0])], text=True)
    badging = subprocess.check_output([str(tools / 'aapt'), 'dump', 'badging', str(apks[0])], text=True)
    result = inspect(badging, certificates, f'{os.environ["C11_VERSION"]}-c11.{os.environ["C11_REVISION"]}',
                     previous_version_code(os.environ['GH_REPO']))
    result.update(upstream_commit=os.environ['C11_UPSTREAM_SHA'], c11_commit=os.environ['GITHUB_SHA'])
    Path('integrated-release/c11-build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
