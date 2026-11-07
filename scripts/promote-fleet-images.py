#!/usr/bin/env python3
"""Update only existing site Fleet workload image pins during release promotion."""
import json
import os
from pathlib import Path
import re

site = os.environ['SITE']
application = os.environ['APPLICATION']
revision = os.environ['RELEASE_SHA']
if (site, application) not in {('wengertsberg','wordpress'),('svu','wordpress'),('sm','redaxo')} or not re.fullmatch(r'[a-f0-9]{40}', revision):
    raise ValueError('Unexpected site or revision')
registry = json.loads((Path(os.environ['ARTIFACT_DIR'])/'registry.json').read_text())
for component, name in [('app', application), ('origin', 'origin')]:
    path = Path('k3s/workloads') / site / component / 'resources.yaml'
    if not path.exists():
        continue  # The original Podman stack remains authoritative until cutover.
    reference = registry[name]
    if not re.fullmatch(rf'ghcr\.io/paul1404/web-services-{site}-{name}@sha256:[a-f0-9]{{64}}', reference):
        raise ValueError('Unexpected image reference')
    value = path.read_text()
    value, count = re.subn(r'(?m)^(\s*)image: \S+\s*\n\1imagePullPolicy: (?:Never|IfNotPresent)\s*$', rf'\1image: {reference}\n\1imagePullPolicy: IfNotPresent', value)
    if count != 1:
        raise ValueError(f'Unexpected deployment image fields: {path}')
    if component == 'origin':
        header = re.compile(r'(header X-[A-Za-z]+-Release (?:\\)?")[a-f0-9]{40}((?:\\)?")')
        if header.search(value):
            value, count = header.subn(lambda m: m[1]+revision+m[2], value)
        else:
            config = path.with_name('config.yaml')
            text = config.read_text()
            text, count = header.subn(lambda m: m[1]+revision+m[2], text)
            if count == 1:
                config.write_text(text)
        if count != 1:
            raise ValueError('Unexpected origin release header')
    path.write_text(value)

# Kubernetes ingress replaces the separate origin over time. Keep the release
# provenance header current while allowing sites without an ingress to use the
# existing promotion path unchanged.
ingress = Path('k3s/workloads') / site / 'origin' / 'ingress.yaml'
if ingress.exists():
    header = {'wengertsberg': 'X-Wengertsberg-Release', 'svu': 'X-SVU-Release', 'sm': 'X-SM-Release'}[site]
    pattern = re.compile(r'(?m)^(\s*' + re.escape(header) + r':\s*)[a-f0-9]{40}$')
    value, count = pattern.subn(lambda match: match[1] + revision, ingress.read_text())
    if count != 1:
        raise ValueError(f'Unexpected ingress release header: {ingress}')
    ingress.write_text(value)
