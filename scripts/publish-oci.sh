#!/bin/bash
# Publish the exact tested release archives. No host credentials are involved.
set -euo pipefail
site="${SITE:?}"; application="${APPLICATION:?}"; artifacts="${ARTIFACT_DIR:?}"
case "$site:$application" in wengertsberg:wordpress|svu:wordpress|sm:redaxo) ;; *) exit 2 ;; esac
printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin >/dev/null
trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT
python3 - "$artifacts/release.json" "$RELEASE_SHA" "$site" <<'PY'
import json,re,sys
r=json.load(open(sys.argv[1])); rev,site=sys.argv[2:]
assert r['source']=={'repository':'Paul1404/web-services','commit':rev}
assert re.fullmatch('[0-9a-f]{40}',rev)
for name,entry in r['images'].items():
 assert entry['url']==f'https://github.com/Paul1404/web-services/releases/download/{site}-{rev}/{name}.tar.gz'
 assert re.fullmatch('[0-9a-f]{64}',entry['sha256']) and re.fullmatch('sha256:[0-9a-f]{64}',entry['id'])
PY
for name in "$application" origin; do
    archive="$artifacts/$name.tar.gz"
    if ! test -f "$archive"; then gh release download "$site-$RELEASE_SHA" --pattern "$name.tar.gz" --dir "$artifacts"; fi
    expected=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["images"][sys.argv[2]]["sha256"])' "$artifacts/release.json" "$name")
    printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status
    image_id=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["images"][sys.argv[2]]["id"])' "$artifacts/release.json" "$name")
    gzip -dc "$archive" | docker load >/dev/null
    docker image inspect "$image_id" >/dev/null
    image="ghcr.io/paul1404/web-services-${site}-${name}:$RELEASE_SHA"
    docker tag "$image_id" "$image"
    docker push "$image" > "$artifacts/$name.push"
    digest=$(sed -nE 's/.*digest: (sha256:[a-f0-9]{64}) .*/\1/p' "$artifacts/$name.push" | tail -n1)
    [[ "$digest" =~ ^sha256:[a-f0-9]{64}$ ]]
    reference="${image%:*}@$digest"
    python3 "$GITHUB_WORKSPACE/scripts/verify-public-oci.py" "$reference" "$image_id"
    printf '%s\n' "$reference" > "$artifacts/$name.reference"
done
python3 - "$artifacts" "$application" <<'PY'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]); names=[sys.argv[2],'origin']
(p/'registry.json').write_text(json.dumps({n:(p/(n+'.reference')).read_text().strip() for n in names},indent=2)+'\n')
PY
