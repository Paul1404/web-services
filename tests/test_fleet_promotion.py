import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/promote-fleet-images.py'
INPUTS_SCRIPT = SCRIPT.with_name('release-inputs-changed.sh')


class FleetPromotionTests(unittest.TestCase):
    def test_promotion_only_changes_do_not_trigger_image_rebuilds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            git('init', '-q')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'Fixture')
            (root / 'site').mkdir()
            (root / 'site/app').write_text('v1')
            (root / 'promotion').write_text('v1')
            git('add', '.')
            git('commit', '-qm', 'initial')
            previous = git('rev-parse', 'HEAD')
            (root / 'promotion').write_text('v2')
            git('add', '.')
            git('commit', '-qm', 'promotion only')
            command = ['bash', str(INPUTS_SCRIPT), previous, 'HEAD', 'site', 'origin']
            self.assertEqual(subprocess.run(command, cwd=root).returncode, 1)
            (root / 'site/app').write_text('v2')
            git('add', '.')
            git('commit', '-qm', 'application change')
            self.assertEqual(subprocess.run(command, cwd=root).returncode, 0)

    def test_ingress_release_revision_is_updated_without_other_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ingress = root / 'k3s/workloads/svu/origin/ingress.yaml'
            ingress.parent.mkdir(parents=True)
            original = 'customResponseHeaders:\n  X-SVU-Release: ' + 'a' * 40 + '\n'
            ingress.write_text(original)
            (root / 'registry.json').write_text('{}')
            env = dict(os.environ, SITE='svu', APPLICATION='wordpress', RELEASE_SHA='b' * 40, ARTIFACT_DIR=directory)
            subprocess.run([sys.executable, str(SCRIPT)], cwd=root, env=env, check=True)
            self.assertEqual(ingress.read_text(), original.replace('a' * 40, 'b' * 40))

    def test_ambiguous_ingress_headers_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ingress = root / 'k3s/workloads/svu/origin/ingress.yaml'
            ingress.parent.mkdir(parents=True)
            original = ('X-SVU-Release: ' + 'a' * 40 + '\n') * 2
            ingress.write_text(original)
            (root / 'registry.json').write_text('{}')
            env = dict(os.environ, SITE='svu', APPLICATION='wordpress', RELEASE_SHA='b' * 40, ARTIFACT_DIR=directory)
            result = subprocess.run([sys.executable, str(SCRIPT)], cwd=root, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(ingress.read_text(), original)
