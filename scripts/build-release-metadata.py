#!/usr/bin/env python3
"""Describe tested site images while retaining unchanged fallback artifacts."""
import hashlib
import json
from pathlib import Path
import re
import sys


def metadata(site, application, revision, app_directory, artifacts, previous, origin_active):
    if (site, application) not in {('wengertsberg', 'wordpress'), ('svu', 'wordpress'), ('sm', 'redaxo')} or not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Unexpected site or revision')
    images = {'database': previous['images']['database'], 'origin': previous['images']['origin']}
    for name in [application] + (['origin'] if origin_active else []):
        digest = hashlib.sha256()
        with (artifacts / (name + '.tar.gz')).open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        image_id = (artifacts / (name + '.id')).read_text().strip()
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', image_id):
            raise ValueError('Unexpected tested image ID')
        images[name] = {'url': f'https://github.com/Paul1404/web-services/releases/download/{site}-{revision}/{name}.tar.gz', 'sha256': digest.hexdigest(), 'id': image_id}
    first_line = (app_directory / 'Dockerfile').read_text().splitlines()[0]
    if not first_line.startswith('FROM '):
        raise ValueError('Unexpected application Dockerfile')
    runtime = first_line.removeprefix('FROM ')
    result = {'source': {'repository': 'Paul1404/web-services', 'commit': revision}, 'images': images}
    if site == 'wengertsberg':
        if not runtime.startswith('wordpress:'):
            raise ValueError('Unexpected WordPress base')
        result['wordpressVersion'] = runtime.removeprefix('wordpress:')
    else:
        result['runtimeVersion'] = runtime
    return result


def main():
    site, application, revision, app_directory, artifacts, previous_file, origin_active = sys.argv[1:]
    previous = json.loads(Path(previous_file).read_text())
    result = metadata(site, application, revision, Path(app_directory), Path(artifacts), previous, origin_active == 'true')
    (Path(artifacts) / 'release.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
