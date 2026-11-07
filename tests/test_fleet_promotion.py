import os
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/promote-fleet-images.py'
INPUTS_SCRIPT = SCRIPT.with_name('release-inputs-changed.sh')
ORIGIN_CHECK_SCRIPT = SCRIPT.with_name('should-verify-origin.sh')
METADATA_SPEC = importlib.util.spec_from_file_location('release_metadata', SCRIPT.with_name('build-release-metadata.py'))
metadata_module = importlib.util.module_from_spec(METADATA_SPEC)
METADATA_SPEC.loader.exec_module(metadata_module)


class FleetPromotionTests(unittest.TestCase):
    def test_origin_check_runs_only_for_origin_or_shared_smoke_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            git('init', '-q')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'Fixture')
            (root / 'app').mkdir()
            (root / 'origin').mkdir()
            (root / 'app/file').write_text('v1')
            (root / 'origin/file').write_text('v1')
            git('add', '.')
            git('commit', '-qm', 'initial')
            previous = git('rev-parse', 'HEAD')
            (root / 'app/file').write_text('v2')
            git('add', '.')
            git('commit', '-qm', 'app only')
            command = ['bash', str(ORIGIN_CHECK_SCRIPT), previous, 'HEAD', 'origin']
            self.assertEqual(subprocess.run(command, cwd=root).returncode, 1)
            (root / 'origin/file').write_text('v2')
            git('add', '.')
            git('commit', '-qm', 'origin changed')
            self.assertEqual(subprocess.run(command, cwd=root).returncode, 0)
            self.assertEqual(subprocess.run(['bash', str(ORIGIN_CHECK_SCRIPT), 'bad-base', 'HEAD', 'origin'], cwd=root).returncode, 0)

    def test_promotion_only_changes_do_not_trigger_image_rebuilds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            git('init', '-q')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'Fixture')
            (root / 'site').mkdir()
            (root / 'origin').mkdir()
            (root / 'site/app').write_text('v1')
            (root / 'origin/proxy').write_text('v1')
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

    def test_retired_origin_changes_do_not_trigger_app_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            git('init', '-q')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'user.name', 'Fixture')
            (root / 'site').mkdir()
            (root / 'origin').mkdir()
            (root / 'site/app').write_text('v1')
            (root / 'origin/proxy').write_text('v1')
            git('add', '.')
            git('commit', '-qm', 'initial')
            previous = git('rev-parse', 'HEAD')
            (root / 'origin/proxy').write_text('v2')
            git('add', '.')
            git('commit', '-qm', 'origin change')
            base = ['bash', str(INPUTS_SCRIPT), previous, 'HEAD', 'site']
            self.assertEqual(subprocess.run([*base, '-'], cwd=root).returncode, 1)
            self.assertEqual(subprocess.run([*base, 'origin'], cwd=root).returncode, 0)

    def test_retired_origin_and_database_artifacts_are_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app_dir = root / 'app'
            app_dir.mkdir()
            (app_dir / 'Dockerfile').write_text('FROM wordpress:7.1.3\n')
            (root / 'wordpress.tar.gz').write_bytes(b'tested-app')
            (root / 'wordpress.id').write_text('sha256:' + 'a' * 64)
            old_origin = {'url': 'https://example.invalid/origin', 'sha256': 'b' * 64, 'id': 'sha256:' + 'c' * 64}
            old_database = {'url': 'https://example.invalid/database', 'sha256': 'd' * 64, 'id': 'sha256:' + 'e' * 64}
            result = metadata_module.metadata('svu', 'wordpress', 'f' * 40, app_dir, root,
                                              {'images': {'origin': old_origin, 'database': old_database}}, False)
            self.assertEqual(result['images']['origin'], old_origin)
            self.assertEqual(result['images']['database'], old_database)
            self.assertIn('svu-' + 'f' * 40 + '/wordpress.tar.gz', result['images']['wordpress']['url'])

    def test_active_origin_still_gets_a_tested_release_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app_dir = root / 'app'
            app_dir.mkdir()
            (app_dir / 'Dockerfile').write_text('FROM wordpress:7.1.3\n')
            for name in ('wordpress', 'origin'):
                (root / (name + '.tar.gz')).write_bytes(('tested-' + name).encode())
                (root / (name + '.id')).write_text('sha256:' + 'a' * 64)
            old = {'url': 'https://example.invalid/old', 'sha256': 'b' * 64, 'id': 'sha256:' + 'c' * 64}
            result = metadata_module.metadata('wengertsberg', 'wordpress', 'f' * 40, app_dir, root,
                                              {'images': {'origin': old, 'database': old}}, True)
            self.assertEqual(result['images']['database'], old)
            self.assertIn('wengertsberg-' + 'f' * 40 + '/origin.tar.gz', result['images']['origin']['url'])
            self.assertEqual(result['wordpressVersion'], '7.1.3')

    def test_oci_publisher_skips_retired_origin_and_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / 'artifacts'
            artifacts.mkdir()
            fake_bin = root / 'bin'
            fake_bin.mkdir()
            (fake_bin / 'docker').write_text(
                '#!/bin/sh\ncase "$1" in\n'
                'login|load) cat >/dev/null;;\n'
                'logout|image|tag) :;;\n'
                'push) case "$2" in *wordpress*|*origin*) printf "digest: sha256:%064d size: 1\\n" 0;; *) exit 9;; esac;;\n'
                '*) exit 9;;\nesac\n')
            (fake_bin / 'docker').chmod(0o755)
            (fake_bin / 'gh').write_text('#!/bin/sh\nexit 9\n')
            (fake_bin / 'gh').chmod(0o755)
            (fake_bin / 'sha256sum').write_text(
                '#!/usr/bin/env python3\nimport hashlib,sys\n'
                'digest,path=sys.stdin.read().strip().split(None,1)\n'
                'sys.exit(0 if hashlib.sha256(open(path.strip(),"rb").read()).hexdigest()==digest else 1)\n')
            (fake_bin / 'sha256sum').chmod(0o755)
            scripts = root / 'scripts'
            scripts.mkdir()
            (scripts / 'verify-public-oci.py').write_text('pass\n')
            config = b'{"fixture":true}'
            image_id = 'sha256:' + hashlib.sha256(config).hexdigest()
            archive_path = artifacts / 'wordpress.tar.gz'
            with tarfile.open(archive_path, 'w:gz') as archive:
                for name, content in [('config.json', config), ('manifest.json', json.dumps([{'Config': 'config.json'}]).encode())]:
                    info = tarfile.TarInfo(name)
                    info.size = len(content)
                    archive.addfile(info, io.BytesIO(content))
            old = {'url': 'https://example.invalid/old', 'sha256': 'a' * 64, 'id': 'sha256:' + 'b' * 64}
            revision = 'c' * 40
            app = {'url': f'https://github.com/Paul1404/web-services/releases/download/svu-{revision}/wordpress.tar.gz',
                   'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(), 'id': image_id}
            (artifacts / 'release.json').write_text(json.dumps({'source': {'repository': 'Paul1404/web-services', 'commit': revision},
                                                               'images': {'wordpress': app, 'origin': old, 'database': old}}))
            env = dict(os.environ, SITE='svu', APPLICATION='wordpress', ARTIFACT_DIR=str(artifacts), RELEASE_SHA=revision,
                       ORIGIN_ACTIVE='false', GH_TOKEN='fixture', GITHUB_ACTOR='fixture', GITHUB_WORKSPACE=str(root),
                       PATH=str(fake_bin) + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['bash', str(SCRIPT.with_name('publish-oci.sh'))], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            registry = json.loads((artifacts / 'registry.json').read_text())
            self.assertEqual(set(registry), {'wordpress'})
            (artifacts / 'origin.tar.gz').write_bytes(archive_path.read_bytes())
            origin = dict(app, url=f'https://github.com/Paul1404/web-services/releases/download/svu-{revision}/origin.tar.gz')
            (artifacts / 'release.json').write_text(json.dumps({'source': {'repository': 'Paul1404/web-services', 'commit': revision},
                                                               'images': {'wordpress': app, 'origin': origin, 'database': old}}))
            env['ORIGIN_ACTIVE'] = 'true'
            result = subprocess.run(['bash', str(SCRIPT.with_name('publish-oci.sh'))], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            registry = json.loads((artifacts / 'registry.json').read_text())
            self.assertEqual(set(registry), {'wordpress', 'origin'})

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
