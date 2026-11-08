#!/bin/bash
set -euo pipefail
test "$GITHUB_REPOSITORY" = Paul1404/web-services
[[ "$RELEASE_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git rev-parse HEAD)" = "$RELEASE_SHA"
site="${SITE:?SITE is required}"
case "$site" in svu) application=wordpress; app_directory=railway-svu-wordpress; origin_directory=railway-svu-origin ;; sm) application=redaxo; app_directory=railway-sm-redaxo; origin_directory=railway-sm-redaxo-origin ;; *) exit 2 ;; esac
export SITE="$site" APPLICATION="$application" APP_DIRECTORY="$app_directory"
test -n "$PROMOTION_KEY"
umask 077
artifact_dir="$RUNNER_TEMP/${site}-artifacts"
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
previous_manifest="$RUNNER_TEMP/desired-state/sites/${site}.json"
pinned=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["source"]["commit"])' "$previous_manifest")
[[ "$pinned" =~ ^[0-9a-f]{40}$ ]]
origin_active=false
origin_input=-
if test -f "$RUNNER_TEMP/desired-state/k3s/workloads/$site/origin/resources.yaml"; then origin_active=true; origin_input="$origin_directory"; fi
export ORIGIN_ACTIVE="$origin_active" PREVIOUS_MANIFEST="$previous_manifest"
# Compare cumulatively with the last desired release. This also catches a site
# change whose CI was superseded by an unrelated documentation commit.
# Promotion-only and workflow edits are checked by CI; they do not change the
# tested site images and should not redeploy an otherwise unchanged site.
if bash "$GITHUB_WORKSPACE/scripts/release-inputs-changed.sh" "$pinned" "$RELEASE_SHA" "$app_directory" "$origin_input"; then
    :
else
    status=$?
    if test "$status" -ne 1; then exit "$status"; fi
    echo 'Website release inputs are unchanged'
    exit 0
fi
tag="${site}-$RELEASE_SHA"
published=false
if gh release view "$tag" --json isDraft > "$artifact_dir/release-status.json" 2>/dev/null; then
    published=$(python3 -c 'import json,sys;print(str(not json.load(open(sys.argv[1]))["isDraft"]).lower())' "$artifact_dir/release-status.json")
fi
if test "$published" = true; then
    gh release download "$tag" --pattern release.json --dir "$artifact_dir"
else
    components=("$application")
    if test "$origin_active" = true; then components+=(origin); fi
    for name in "${components[@]}"; do
        case "$name" in
            "$application") directory="$app_directory" ;;
            origin) directory="$origin_directory" ;;
        esac
        image="local/${site}-$name:$RELEASE_SHA"
        docker build --pull --label "org.opencontainers.image.revision=$RELEASE_SHA" -t "$image" "$directory"
        python3 tests/release-smoke.py "$directory" "$image"
        docker image inspect --format '{{.Id}}' "$image" > "$artifact_dir/$name.id"
        docker save "$image" | gzip -n > "$artifact_dir/$name.tar.gz"
    done
    python3 "$GITHUB_WORKSPACE/scripts/build-release-metadata.py" "$site" "$application" "$RELEASE_SHA" "$app_directory" "$artifact_dir" "$previous_manifest" "$origin_active"
    if ! gh release view "$tag" >/dev/null 2>&1; then
        gh release create "$tag" --target "$RELEASE_SHA" --draft --title "Website $RELEASE_SHA" --notes 'Tested container archives for pull-based deployment. Digests and image IDs are in release.json. Website data and secrets are excluded.'
    fi
    assets=("$artifact_dir/$application.tar.gz" "$artifact_dir/release.json")
    if test "$origin_active" = true; then assets+=("$artifact_dir/origin.tar.gz"); fi
    gh release upload "$tag" "${assets[@]}" --clobber
    gh release edit "$tag" --draft=false
fi
export ARTIFACT_DIR="$artifact_dir"
bash "$GITHUB_WORKSPACE/scripts/publish-oci.sh"
cd "$RUNNER_TEMP/desired-state"
git fetch --quiet origin main
git reset --hard origin/main
git switch -c "releases/${site}-$RELEASE_SHA"
ARTIFACT_DIR="$artifact_dir" python3 - <<'PY'
import json,os,pathlib
p=pathlib.Path('sites')/(os.environ['SITE']+'.json');current=json.loads(p.read_text())
release=json.loads((pathlib.Path(os.environ['ARTIFACT_DIR'])/'release.json').read_text())
assert release['source']=={'repository':'Paul1404/web-services','commit':os.environ['RELEASE_SHA']}
database=current['images'].get('database')
origin=current['images'].get('origin')
current.update(source=release['source'],runtimeVersion=release['runtimeVersion'],images=release['images'])
if database:current['images']['database']=database
if os.environ['ORIGIN_ACTIVE']=='false':current['images']['origin']=origin
p.write_text(json.dumps(current,indent=2)+'\n')
PY
ARTIFACT_DIR="$artifact_dir" python3 - <<'PYCODE'
import json, os, pathlib, re
site=os.environ['SITE']; app=os.environ['APPLICATION']; assert (site,app) in {('svu','wordpress'),('sm','redaxo')}
registry=json.loads((pathlib.Path(os.environ['ARTIFACT_DIR'])/'registry.json').read_text());image=registry[app]
assert re.fullmatch(r'ghcr\.io/paul1404/web-services-'+site+'-'+app+r'@sha256:[a-f0-9]{64}',image)
p=pathlib.Path('workloads')/site/'resources.yaml';s,n=re.subn(r'(?m)^(\s*image: )ghcr\.io/paul1404/web-services-'+site+'-'+app+r'@sha256:[a-f0-9]{64}$',lambda m:m[1]+image,p.read_text());assert n==1;p.write_text(s)
header={'svu':'X-SVU-Release','sm':'X-SM-Release'}[site];p=pathlib.Path('workloads')/site/'route.yaml';s,n=re.subn(r'(?m)^(\s*'+header+r': )[a-f0-9]{40}$',lambda m:m[1]+os.environ['RELEASE_SHA'],p.read_text());assert n==1;p.write_text(s)
PYCODE
if git diff --quiet; then
    echo 'Release is already desired state'
    exit 0
fi
git config user.name 'Website release automation'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add sites/${site}.json workloads/${site}/resources.yaml workloads/${site}/route.yaml
for component in app origin; do
    path="k3s/workloads/$SITE/$component/resources.yaml"
    if test -f "$path"; then git add "$path"; fi
done
config="k3s/workloads/$SITE/origin/config.yaml"
if test -f "$config"; then git add "$config"; fi
ingress="k3s/workloads/$SITE/origin/ingress.yaml"
if test -f "$ingress"; then git add "$ingress"; fi
git commit -m "Promote tested Website $RELEASE_SHA"
for attempt in 1 2 3; do
    git fetch --quiet origin main
    git rebase origin/main
    if git push origin HEAD:main; then exit 0; fi
done
echo 'Unable to promote after concurrent updates' >&2
exit 1
