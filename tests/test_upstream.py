import importlib.util
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1]/'scripts/sync_upstream.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

def release(tag='v0.2.21', draft=False, digest='sha256:'+'a'*64):
    version=tag[1:]
    return {'tag_name':tag, 'draft':draft, 'prerelease':True, 'assets':[
        {'name':f'DiPlay-{version}.apk','digest':digest},
        {'name':f'DiPlay-{version}-source.zip','digest':digest}]}

class ReleaseTests(unittest.TestCase):
    def test_includes_upstream_prereleases(self):
        self.assertEqual('v0.2.21', sync.select_release([release()])[0]['tag_name'])
    def test_drafts_are_ignored(self):
        self.assertEqual('v0.2.20', sync.select_release([release(draft=True),release('v0.2.20')])[0]['tag_name'])
    def test_missing_source_rejected(self):
        r=release();r['assets'].pop()
        with self.assertRaises(ValueError):sync.select_release([r])
    def test_missing_digest_rejected(self):
        with self.assertRaises(ValueError):sync.select_release([release(digest=None)])
    def test_arbitrary_tag_rejected(self):
        with self.assertRaises(ValueError):sync.select_release([release('v0.2.21/unsafe')])
    def test_download_integrity(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.apk';path.write_bytes(b'abc')
            sync.verify(path,'sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
            with self.assertRaises(ValueError):sync.verify(path,'sha256:'+'a'*64)

if __name__=='__main__':unittest.main()
