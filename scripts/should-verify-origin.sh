#!/usr/bin/env bash
# Exit 0 to run the origin image check, 1 when its relevant inputs are unchanged.
set -euo pipefail
base="$1"
revision="$2"
directory="$3"
if [[ ! "$base" =~ ^[a-f0-9]{40}$ ]] || ! git cat-file -e "$base^{commit}" 2>/dev/null; then
    exit 0
fi
if git diff --quiet "$base" "$revision" -- "$directory" tests/release-smoke.py tests/origin-smoke.sh .github/workflows/ci.yml; then
    exit 1
else
    status=$?
    if [[ "$status" -eq 1 ]]; then exit 0; fi
    exit "$status"
fi
