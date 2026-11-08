#!/bin/bash
set -euo pipefail
test "$GITHUB_REPOSITORY" = Paul1404/web-services
[[ "$RELEASE_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git rev-parse HEAD)" = "$RELEASE_SHA"
test -n "$PROMOTION_KEY"
umask 077
export SITE=wengertsberg APPLICATION=wordpress
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
git clone --quiet git@github.com:Paul1404/vertex-fleet.git "$RUNNER_TEMP/desired-state"
previous_manifest="$RUNNER_TEMP/desired-state/sites/wengertsberg.json"
pinned=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["source"]["commit"])' "$previous_manifest")
[[ "$pinned" =~ ^[0-9a-f]{40}$ ]]
origin_active=false
origin_input=-
if test -f "$RUNNER_TEMP/desired-state/k3s/workloads/wengertsberg/origin/resources.yaml"; then origin_active=true; origin_input=railway-wengertsberg-origin; fi
export ORIGIN_ACTIVE="$origin_active" PREVIOUS_MANIFEST="$previous_manifest"
# Compare cumulatively with the last desired release. This also catches a site
# change whose CI was superseded by an unrelated documentation commit.
# Promotion-only and workflow edits are checked by CI; they do not change the
# tested site images and should not redeploy an otherwise unchanged site.
if bash "$GITHUB_WORKSPACE/scripts/release-inputs-changed.sh" "$pinned" "$RELEASE_SHA" railway-wengertsberg-wordpress "$origin_input"; then
    :
else
    status=$?
    if test "$status" -ne 1; then exit "$status"; fi
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
    components=(wordpress)
    if test "$origin_active" = true; then components+=(origin); fi
    for name in "${components[@]}"; do
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
    python3 "$GITHUB_WORKSPACE/scripts/build-release-metadata.py" wengertsberg wordpress "$RELEASE_SHA" railway-wengertsberg-wordpress "$artifact_dir" "$previous_manifest" "$origin_active"
    if ! gh release view "$tag" >/dev/null 2>&1; then
        gh release create "$tag" --target "$RELEASE_SHA" --draft --title "Wengertsberg $RELEASE_SHA" --notes 'Tested container archives for pull-based deployment. Digests and image IDs are in release.json. Website data and secrets are excluded.'
    fi
    assets=("$artifact_dir/wordpress.tar.gz" "$artifact_dir/release.json")
    if test "$origin_active" = true; then assets+=("$artifact_dir/origin.tar.gz"); fi
    gh release upload "$tag" "${assets[@]}" --clobber
    gh release edit "$tag" --draft=false
fi
export ARTIFACT_DIR="$artifact_dir"
bash "$GITHUB_WORKSPACE/scripts/publish-oci.sh"
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
origin=current['images'].get('origin')
current.update(source=release['source'],wordpressVersion=release['wordpressVersion'],images=release['images'])
if database:current['images']['database']=database
if os.environ['ORIGIN_ACTIVE']=='false':current['images']['origin']=origin
p.write_text(json.dumps(current,indent=2)+'\n')
PY
ARTIFACT_DIR="$artifact_dir" python3 - <<'PYCODE'
import json, os, pathlib, re
registry=json.loads((pathlib.Path(os.environ['ARTIFACT_DIR'])/'registry.json').read_text())
image=registry['wordpress']
assert re.fullmatch(r'ghcr\.io/paul1404/web-services-wengertsberg-wordpress@sha256:[a-f0-9]{64}',image)
p=pathlib.Path('workloads/wengertsberg/resources.yaml')
s,n=re.subn(r'(?m)^(\s*image: )ghcr\.io/paul1404/web-services-wengertsberg-wordpress@sha256:[a-f0-9]{64}$',lambda m:m[1]+image,p.read_text()); assert n==1; p.write_text(s)
p=pathlib.Path('workloads/wengertsberg/route.yaml')
s,n=re.subn(r'(?m)^(\s*X-Wengertsberg-Release: )[a-f0-9]{40}$',lambda m:m[1]+os.environ['RELEASE_SHA'],p.read_text()); assert n==1;p.write_text(s)
PYCODE
if git diff --quiet; then
    echo 'Release is already desired state'
    exit 0
fi
git config user.name 'Wengertsberg release automation'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add sites/wengertsberg.json workloads/wengertsberg/resources.yaml workloads/wengertsberg/route.yaml
for component in app origin; do
    path="k3s/workloads/$SITE/$component/resources.yaml"
    if test -f "$path"; then git add "$path"; fi
done
config="k3s/workloads/$SITE/origin/config.yaml"
if test -f "$config"; then git add "$config"; fi
ingress="k3s/workloads/$SITE/origin/ingress.yaml"
if test -f "$ingress"; then git add "$ingress"; fi
git commit -m "Promote tested Wengertsberg $RELEASE_SHA"
for attempt in 1 2 3; do
    git fetch --quiet origin main
    git rebase origin/main
    if git push origin HEAD:main; then exit 0; fi
done
echo 'Unable to promote after concurrent updates' >&2
exit 1
