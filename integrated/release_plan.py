from pathlib import Path
import json,subprocess,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_upstream import select_release
config=json.loads(Path('integrated/config.json').read_text())
release,_=select_release(json.loads(subprocess.check_output(['gh','api',f'repos/shihabal3amri/DiPlay/releases?per_page=10'])))
version=release['tag_name'][1:];tag=f'c11-v{version}-c11.{config["revision"]}'
releases=json.loads(subprocess.check_output(['gh','api',f'repos/{os.environ["GH_REPO"]}/releases?per_page=100']))
needed=not any(r['tag_name']==tag for r in releases)
with open(os.environ['GITHUB_OUTPUT'],'a') as out:
    for key,value in {'needed':str(needed).lower(),'tag':tag,'upstream_tag':release['tag_name'],'version':version,'revision':config['revision']}.items():out.write(f'{key}={value}\n')
print('C11 integrated plan:',tag,'needed='+str(needed))
