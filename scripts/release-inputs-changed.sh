#!/usr/bin/env bash
# Exit 0 when a site needs a new image release, 1 when its inputs are unchanged.
set -euo pipefail
previous="$1"
revision="$2"
application="$3"
origin="$4"
if [[ "$previous" == 0000000000000000000000000000000000000000 ]] || ! git cat-file -e "$previous^{commit}" 2>/dev/null; then
    exit 0
fi
inputs=("$application")
if [[ "$origin" != '-' ]]; then inputs+=("$origin"); fi
if git diff --quiet "$previous" "$revision" -- "${inputs[@]}"; then
    exit 1
else
    status=$?
    if [[ "$status" -eq 1 ]]; then exit 0; fi
    exit "$status"
fi
