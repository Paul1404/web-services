#!/bin/bash
set -euo pipefail
test "$GITHUB_REPOSITORY" = Paul1404/web-services
[[ "$RELEASE_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git rev-parse HEAD)" = "$RELEASE_SHA"
test -n "$PROMOTION_KEY"
umask 077
artifact_dir="$RUNNER_TEMP/wengertsberg-artifacts"
mkdir -p "$artifact_dir"
# The key is scoped only to the private desired-state repository. No host key,
# website runtime credential or mail credential is available to this workflow.
printf '%s\n' "$PROMOTION_KEY" > "$RUNNER_TEMP/promotion-key"
unset PROMOTION_KEY
gh api meta > "$RUNNER_TEMP/github-meta.json"
RUNNER_TEMP="$RUNNER_TEMP" python3 - <<'PY'
import json,os,pathlib
p=pathlib.Path(os.environ['RUNNER_TEMP'])
keys=[x for x in json.loads((p/'github-meta.json').read_text())['ssh_keys'] if x.startswith('ssh-ed25519 ')]
assert len(keys)==1
(p/'promotion-known-hosts').write_text('github.com '+keys[0]+'\n')
(p/'promotion-ssh-config').write_text(f'Host github.com\n HostName ssh.github.com\n Port 443\n User git\n HostKeyAlias github.com\n IdentityFile {p}/promotion-key\n IdentitiesOnly yes\n StrictHostKeyChecking yes\n UserKnownHostsFile {p}/promotion-known-hosts\n')
PY
export GIT_SSH_COMMAND="ssh -F $RUNNER_TEMP/promotion-ssh-config"
git clone --quiet git@github.com:Paul1404/web-host-gitops.git "$RUNNER_TEMP/desired-state"
pinned=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["source"]["commit"])' "$RUNNER_TEMP/desired-state/sites/wengertsberg.json")
[[ "$pinned" =~ ^[0-9a-f]{40}$ ]]
# Compare cumulatively with the last desired release. This also catches a site
# change whose CI was superseded by an unrelated documentation commit.
if test "$pinned" != 0000000000000000000000000000000000000000 && git cat-file -e "$pinned^{commit}" 2>/dev/null && git diff --quiet "$pinned" "$RELEASE_SHA" -- railway-wengertsberg-wordpress railway-wengertsberg-origin scripts/publish-wengertsberg.sh .github/workflows/publish-wengertsberg.yml; then
    echo 'Wengertsberg release inputs are unchanged'
    exit 0
fi
tag="wengertsberg-$RELEASE_SHA"
published=false
if gh release view "$tag" --json isDraft > "$artifact_dir/release-status.json" 2>/dev/null; then
    published=$(python3 -c 'import json,sys;print(str(not json.load(open(sys.argv[1]))["isDraft"]).lower())' "$artifact_dir/release-status.json")
fi
if test "$published" = true; then
    gh release download "$tag" --pattern release.json --dir "$artifact_dir"
else
    for name in wordpress origin; do
        case "$name" in
            wordpress) directory=railway-wengertsberg-wordpress ;;
            origin) directory=railway-wengertsberg-origin ;;
        esac
        image="local/wengertsberg-$name:$RELEASE_SHA"
        docker build --pull --label "org.opencontainers.image.revision=$RELEASE_SHA" -t "$image" "$directory"
        python3 tests/release-smoke.py "$directory" "$image"
        docker image inspect --format '{{.Id}}' "$image" > "$artifact_dir/$name.id"
        docker save "$image" | gzip -n > "$artifact_dir/$name.tar.gz"
    done
    docker pull mariadb:12.3
    docker image inspect --format '{{.Id}}' mariadb:12.3 > "$artifact_dir/database.id"
    docker save mariadb:12.3 | gzip -n > "$artifact_dir/database.tar.gz"
    ARTIFACT_DIR="$artifact_dir" python3 - <<'PY'
import hashlib,json,os,pathlib,re
p=pathlib.Path(os.environ['ARTIFACT_DIR']);sha=os.environ['RELEASE_SHA']
version=re.search(r'^FROM wordpress:([^\s]+)',pathlib.Path('railway-wengertsberg-wordpress/Dockerfile').read_text(),re.M)[1]
images={}
for name in ['wordpress','origin','database']:
    with (p/(name+'.tar.gz')).open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    images[name]={'url':f'https://github.com/Paul1404/web-services/releases/download/wengertsberg-{sha}/{name}.tar.gz','sha256':digest,'id':(p/(name+'.id')).read_text().strip()}
(p/'release.json').write_text(json.dumps({'source':{'repository':'Paul1404/web-services','commit':sha},'wordpressVersion':version,'images':images},indent=2)+'\n')
PY
    if ! gh release view "$tag" >/dev/null 2>&1; then
        gh release create "$tag" --target "$RELEASE_SHA" --draft --title "Wengertsberg $RELEASE_SHA" --notes 'Tested container archives for pull-based deployment. Digests and image IDs are in release.json. Website data and secrets are excluded.'
    fi
    gh release upload "$tag" "$artifact_dir/wordpress.tar.gz" "$artifact_dir/origin.tar.gz" "$artifact_dir/database.tar.gz" "$artifact_dir/release.json" --clobber
    gh release edit "$tag" --draft=false
fi
cd "$RUNNER_TEMP/desired-state"
git fetch --quiet origin main
git reset --hard origin/main
git switch -c "releases/wengertsberg-$RELEASE_SHA"
ARTIFACT_DIR="$artifact_dir" python3 - <<'PY'
import json,os,pathlib
p=pathlib.Path('sites/wengertsberg.json');current=json.loads(p.read_text())
release=json.loads((pathlib.Path(os.environ['ARTIFACT_DIR'])/'release.json').read_text())
assert release['source']=={'repository':'Paul1404/web-services','commit':os.environ['RELEASE_SHA']}
database=current['images'].get('database')
current.update(source=release['source'],wordpressVersion=release['wordpressVersion'],images=release['images'])
if database:current['images']['database']=database
p.write_text(json.dumps(current,indent=2)+'\n')
PY
if git diff --quiet; then
    echo 'Release is already desired state'
    exit 0
fi
git config user.name 'Wengertsberg release automation'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add sites/wengertsberg.json
git commit -m "Promote tested Wengertsberg $RELEASE_SHA"
git push origin "releases/wengertsberg-$RELEASE_SHA"
