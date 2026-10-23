import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integrated'))
sys.path.insert(0, str(ROOT / 'scripts'))
import release_plan
import verify_apk
import verify_contract
import sync_upstream
from test_upstream import release


def own(version='0.2.21', revision=104):
    return dict(tag_name=f'c11-v{version}-c11.{revision}', draft=False, assets=[dict(name=name) for name in [
        f'DiPlay-C11-{version}-c11.{revision}.apk', 'DiPlay-C11-source.zip',
        'C11-Integrated-Guide-ZH.md', 'SHA256SUMS.txt', 'upstream.json']])


class SyncPlanningTests(unittest.TestCase):
    config = dict(upstream='shihabal3amri/DiPlay', revision=104)

    def test_release_selection_is_numeric_not_api_order(self):
        self.assertEqual('v0.2.100', sync_upstream.select_release([
            release('v0.2.9'), release('v0.2.99'), release('v0.2.100'), release('v0.2.10')])[0]['tag_name'])

    def test_incomplete_newest_waits_until_assets_are_ready(self):
        newest = release('v0.2.22'); newest['assets'].pop()
        self.assertEqual('v0.2.21', sync_upstream.select_release([newest, release()])[0]['tag_name'])

    def test_pagination_includes_later_pages(self):
        with patch.object(sync_upstream.subprocess, 'check_output', return_value=json.dumps([[release()], [release('v0.2.22')]]).encode()) as command:
            self.assertEqual(2, len(sync_upstream.list_releases('shihabal3amri/DiPlay')))
            self.assertIn('--paginate', command.call_args[0][0])

    def test_current_release_is_idempotent(self):
        self.assertEqual('false', release_plan.make_plan(self.config, [release()], [own()])['needed'])

    def test_new_upstream_build_retains_c11_revision(self):
        plan = release_plan.make_plan(self.config, [release(), release('v0.2.22')], [own()])
        self.assertEqual('true', plan['needed'])
        self.assertEqual('c11-v0.2.22-c11.104', plan['tag'])

    def test_no_downgrade_when_upstream_temporarily_omits_a_release(self):
        self.assertEqual('false', release_plan.make_plan(self.config, [release()], [own('0.2.22')])['needed'])

    def test_existing_partial_release_is_never_overwritten(self):
        broken = own(); broken['assets'].pop()
        with self.assertRaisesRegex(ValueError, 'refusing to overwrite'):
            release_plan.make_plan(self.config, [release()], [broken])

    def test_draft_c11_release_is_not_treated_as_success(self):
        draft = own(); draft['draft'] = True
        with self.assertRaises(ValueError): release_plan.make_plan(self.config, [release()], [draft])

    def test_new_release_resolves_and_outputs_exact_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'output'
            with patch.dict('os.environ', {'GH_REPO': 'meiti789789/DiPlay-C11', 'GITHUB_OUTPUT': str(output)}), \
                    patch.object(release_plan, 'list_releases', side_effect=[[release('v0.2.22')], [own()]]), \
                    patch.object(release_plan.subprocess, 'check_output', return_value=json.dumps({'sha': 'a'*40}).encode()) as command:
                release_plan.main()
                self.assertIn('upstream_sha='+'a'*40, output.read_text())
                self.assertIn('repos/shihabal3amri/DiPlay/commits/v0.2.22', command.call_args[0][0])

    def test_workflow_keeps_full_checks_and_uses_immutable_commit(self):
        workflow = (ROOT / '.github/workflows/integrated.yml').read_text()
        self.assertIn("cron: '47 */6 * * *'", workflow)
        self.assertIn('ref: ${{ needs.plan.outputs.upstream_sha }}', workflow)
        self.assertIn('python3 integrated/verify_contract.py upstream', workflow)
        self.assertIn('python3 integrated/verify_apk.py', workflow)
        for task in [':shared:testDebugUnitTest', ':common:testDebugUnitTest', ':home:testDebugUnitTest',
                     ':mobile:lintDebug', ':home:lintDebug', ':maphost:lintDebug',
                     ':mobile:assembleDebug', ':home:assembleDebug', ':maphost:assembleDebug']:
            self.assertIn(task, workflow)


class ApkIdentityTests(unittest.TestCase):
    def badge(self, package='com.c11.diplay', code=41104, sdk=24):
        return f"package: name='{package}' versionCode='{code}' versionName='0.2.22-c11.104'\nsdkVersion:'{sdk}'\n"

    def inspect(self, badge, digest=verify_apk.SIGNER):
        return verify_apk.inspect(badge, 'Signer #1 certificate SHA-256 digest: '+digest,
                                  '0.2.22-c11.104', 40104)

    def test_same_identity_new_version_passes(self):
        self.assertEqual(41104, self.inspect(self.badge())['version_code'])

    def test_changed_package_or_signer_rejected(self):
        with self.assertRaises(ValueError): self.inspect(self.badge(package='com.shihab.diplay'))
        with self.assertRaises(ValueError): self.inspect(self.badge(), 'a'*64)

    def test_android_9_support_is_required(self):
        with self.assertRaisesRegex(ValueError, 'Android 9'): self.inspect(self.badge(sdk=29))

    def test_nonincreasing_code_rejected(self):
        for code in [40104, 40103]:
            with self.assertRaisesRegex(ValueError, 'versionCode'): self.inspect(self.badge(code=code))


class SourcePreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.target = Path(self.temp.name)
        shutil.copytree(ROOT / 'integrated/overlay', self.target, dirs_exist_ok=True)
        for relative, snippets in verify_contract.REQUIRED.items():
            path = self.target / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('\n'.join(snippets))
        expected = json.loads((ROOT / 'integrated/protected_settings.json').read_text())
        path = self.target / 'common/src/main/java/com/shilapi/xcertplay/AirPlayPersistence.kt'
        path.write_text('\n'.join(f'const val {key} = "{value}"' for key, value in expected.items()))
        path = self.target / 'mobile/build.gradle.kts'; path.parent.mkdir(exist_ok=True)
        path.write_text('applicationId = "com.c11.diplay"')

    def tearDown(self): self.temp.cleanup()

    def test_all_protected_files_and_keys_present(self):
        self.assertGreater(verify_contract.verify(self.target)['preserved_settings_keys'], 100)

    def test_missing_wheel_bridge_or_brand_asset_stops_build(self):
        for relative in ['common/src/main/java/com/shilapi/xcertplay/C11WheelKeys.kt',
                         'common/src/main/res/raw/ic_car_home.png']:
            path = self.target / relative; original = path.read_bytes(); path.unlink()
            with self.assertRaisesRegex(ValueError, 'overlay'): verify_contract.verify(self.target)
            path.write_bytes(original)

    def test_silent_change_to_preference_storage_stops_build(self):
        path = self.target / 'common/src/main/java/com/shilapi/xcertplay/AirPlayPersistence.kt'
        path.write_text(path.read_text().replace('xcertplay_airplay', 'new_empty_preferences'))
        with self.assertRaisesRegex(ValueError, 'preference key'): verify_contract.verify(self.target)

    def test_loss_of_instrument_frame_gate_hook_stops_build(self):
        path = self.target / 'common/src/main/java/com/shilapi/xcertplay/ClusterMapPresentation.kt'
        path.write_text(path.read_text().replace('onC11FrameUpdated()', 'Unit'))
        with self.assertRaisesRegex(ValueError, 'behavior contract'): verify_contract.verify(self.target)


if __name__ == '__main__': unittest.main()
