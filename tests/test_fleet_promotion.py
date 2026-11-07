import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/promote-fleet-images.py'


class FleetPromotionTests(unittest.TestCase):
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
