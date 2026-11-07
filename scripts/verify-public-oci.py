#!/usr/bin/env python3
"""Prove an immutable GHCR reference is public and contains the tested image."""
import hashlib
import json
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

reference, image_id = sys.argv[1:]
match = re.fullmatch(r'ghcr\.io/(paul1404/web-services-(?:wengertsberg|svu|sm)-(?:wordpress|redaxo|origin))@(sha256:[a-f0-9]{64})', reference)
if not match or not re.fullmatch(r'sha256:[a-f0-9]{64}', image_id):
    raise ValueError('Unexpected image reference')
repository, digest = match.groups()
query = urlencode({'scope': 'repository:' + repository + ':pull'})
with urlopen('https://ghcr.io/token?' + query, timeout=30) as response:
    token = json.load(response)['token']
request = Request('https://ghcr.io/v2/' + repository + '/manifests/' + digest, headers={
    'Authorization': 'Bearer ' + token,
    'Accept': 'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json',
})
with urlopen(request, timeout=30) as response:
    raw = response.read()
manifest = json.loads(raw)
if 'sha256:' + hashlib.sha256(raw).hexdigest() != digest or manifest.get('config', {}).get('digest') != image_id:
    raise ValueError('Registry manifest differs from the approved image')
print('Verified public immutable image:', reference)
