import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrated'))
import ota_release
import notify_failure
import report_failure
from test_integrated_sync import own


class OtaReleaseTests(unittest.TestCase):
    def test_numerical_order_handles_9_10_99_100(self):
        for revisions in [[9, 100, 10, 99], [99, 10, 9, 100]]:
            versions = [own(revision=r) for r in revisions]
            with self.assertRaisesRegex(ValueError, '首条'):
                ota_release.validate_catalog(versions, 'c11-v0.2.21-c11.100')
            newest = own(revision=100)
            self.assertEqual(newest, ota_release.validate_catalog([newest] + versions, newest['tag_name']))

    def test_upstream_version_then_revision_sort(self):
        new = own('0.2.22', 104)
        old = own('0.2.21', 999)
        self.assertEqual(new, ota_release.validate_catalog([new, old], new['tag_name']))
        with self.assertRaisesRegex(ValueError, '数字'):
            ota_release.validate_catalog([old, new], old['tag_name'])

    def test_incomplete_or_draft_is_never_offered(self):
        new = own(); new['assets'].pop()
        with self.assertRaises(ValueError): ota_release.validate_catalog([new], new['tag_name'])
        new = own(); new['draft'] = True
        with self.assertRaises(ValueError): ota_release.validate_catalog([new], new['tag_name'])

    def test_failed_public_ota_check_retracts_only_new_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); (folder / 'new.apk').write_bytes(b'APK')
            with patch.dict(os.environ, {'GITHUB_SHA': 'a'*40}), \
                    patch.object(ota_release.subprocess, 'run') as command, \
                    patch.object(ota_release, 'verify_public', side_effect=ValueError('checksum mismatch')), \
                    patch.object(ota_release.time, 'sleep'):
                with self.assertRaisesRegex(ValueError, 'OTA'):
                    ota_release.publish('meiti789789/DiPlay-C11', 'c11-v0.2.22-c11.104', folder)
                calls = [call.args[0] for call in command.call_args_list]
                self.assertIn('--draft', calls[0])
                self.assertIn('--draft=false', calls[1])
                self.assertIn('--draft=true', calls[-1])
                self.assertTrue(all('c11-v0.2.22-c11.104' in call for call in calls))

    def test_successful_ota_check_keeps_release_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); (folder / 'new.apk').write_bytes(b'APK')
            with patch.dict(os.environ, {'GITHUB_SHA': 'a'*40}), \
                    patch.object(ota_release.subprocess, 'run') as command, \
                    patch.object(ota_release, 'verify_public', return_value={'verified': True}):
                self.assertTrue(ota_release.publish('meiti789789/DiPlay-C11', 'c11-v0.2.22-c11.104', folder)['verified'])
                self.assertEqual(2, command.call_count)


class FailureNotificationTests(unittest.TestCase):
    def test_delivery_test_is_clearly_marked_and_does_not_claim_real_failure(self):
        title, body = notify_failure.test_message('meiti789789/DiPlay-C11', 123, 1)
        self.assertIn('通知链路测试', title)
        self.assertIn('@meiti789789', body)
        self.assertIn('没有发生真实同步失败', body)
        self.assertIn('[测试示例]', body)
        self.assertNotIn('本次 C11 自动同步／更新失败。', body)

    def test_failure_message_mentions_owner_with_reason_test_and_log(self):
        title, body = notify_failure.message('meiti789789/DiPlay-C11', 123, 2, [
            {'conclusion':'failure','steps':[{'name':'All checks required by upstream AGENTS.md','conclusion':'failure'}]}],
            {'direct_reason':'RuntimeError: Upstream anchor changed',
             'failed_tests':[{'test':'testMarker','error':'java.lang.AssertionError'}]})
        self.assertIn('@meiti789789', body)
        self.assertIn('Upstream anchor changed', body)
        self.assertIn('testMarker', body)
        self.assertIn('/actions/runs/123/attempts/2', body)
        self.assertIn('第 2 次', title)

    def test_test_report_exports_name_and_type_without_raw_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root/'common/build/reports/tests/testDebugUnitTest/test.html'
            file.parent.mkdir(parents=True)
            file.write_text('<pre id="root-0-test-failure-testMarker">java.lang.AssertionError: sensitive-value</pre>')
            result = report_failure.report(root, root/'missing.json')
            self.assertEqual([dict(test='testMarker',error='java.lang.AssertionError')], result['failed_tests'])
            self.assertNotIn('sensitive-value', json.dumps(result))

    def test_workflow_notifies_plan_or_build_failure_but_not_cancellation(self):
        workflow = (Path(__file__).resolve().parents[1]/'.github/workflows/integrated.yml').read_text()
        self.assertIn("needs.plan.result == 'failure' || needs.build.result == 'failure'", workflow)
        self.assertIn('issues: write', workflow)
        self.assertIn('python3 integrated/notify_failure.py', workflow)
        self.assertIn('python3 integrated/run_guarded.py python3 integrated/ota_release.py', workflow)


if __name__ == '__main__': unittest.main()
