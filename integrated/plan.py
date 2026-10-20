from pathlib import Path
import json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_upstream import select_release
config=json.loads(Path('integrated/config.json').read_text())
release,assets=select_release(json.loads(subprocess.check_output(['gh','api',f'repos/{config["upstream"]}/releases?per_page=10'])))
version=release['tag_name'][1:]
with open(os.environ['GITHUB_OUTPUT'],'a') as out:
    out.write(f'upstream_tag={release["tag_name"]}\nversion={version}\nrevision={config["revision"]}\n')
print('Checking upstream',release['tag_name'],'C11 revision',config['revision'])
