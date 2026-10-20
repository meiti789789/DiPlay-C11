"""Owner-authorized reuse of the experimental accessory identity in a public upstream APK.
Never imports Android signing keys, vehicle/account credentials or unpublished identities.
"""
from pathlib import Path
import os,json,hashlib,subprocess,zipfile,re

tag=os.environ['C11_UPSTREAM_TAG']
if not re.fullmatch(r'v\d+\.\d+\.\d+',tag):raise ValueError('Invalid upstream release tag')
release=json.loads(subprocess.check_output(['gh','api',f'repos/shihabal3amri/DiPlay/releases/tags/{tag}']))
name=f'DiPlay-{tag[1:]}.apk'
asset=next(a for a in release['assets'] if a['name']==name)
if not re.fullmatch(r'sha256:[0-9a-f]{64}',asset.get('digest') or ''):raise ValueError('Missing upstream SHA256')
folder=Path(os.environ['RUNNER_TEMP'],'c11-authorized-public-apk');folder.mkdir(mode=0o700,exist_ok=True)
subprocess.run(['gh','release','download',tag,'--repo','shihabal3amri/DiPlay','--pattern',name,'--dir',str(folder)],check=True)
apk=folder/name
if 'sha256:'+hashlib.sha256(apk.read_bytes()).hexdigest()!=asset['digest']:raise ValueError('Upstream APK checksum mismatch')
assets=Path(os.environ['RUNNER_TEMP'],'c11-authorized-runtime-assets')
with zipfile.ZipFile(apk) as archive:
    for filename in ['identity.pk8','certificate.p7b']:
        target=assets/'offline-mfi'/filename;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        target.write_bytes(archive.read('assets/offline-mfi/'+filename));target.chmod(0o600)
with open(os.environ['GITHUB_ENV'],'a') as env:env.write('DIPLAY_AUTH_ASSETS_DIR='+str(assets)+'\n')
Path(os.environ['RUNNER_TEMP'],'c11-runtime-provenance.json').write_text(json.dumps({
    'source_release':release['html_url'],'source_apk':name,'sha256':asset['digest'],
    'notice':'Owner-authorized reuse of already-public experimental accessory identity; not Apple certification; no Android signing secrets from upstream.',
},indent=2)+'\n')
print('Matched and SHA256-verified the authorized public upstream APK; runtime assets outside source.')
