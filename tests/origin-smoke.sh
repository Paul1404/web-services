#!/bin/bash
set -euo pipefail
image=${1:?image required}
container="web-services-origin-test-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true' EXIT
docker run --rm --entrypoint caddy \
  -e ORIGIN_VERIFY=smoke-test-only \
  -e WORDPRESS_UPSTREAM=http://127.0.0.1:9999 \
  -e REDAXO_UPSTREAM=http://127.0.0.1:9999 \
  "$image" validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker run -d --name "$container" -p 127.0.0.1::8080 \
  -e ORIGIN_VERIFY=smoke-test-only \
  -e WORDPRESS_UPSTREAM=http://127.0.0.1:9999 \
  -e REDAXO_UPSTREAM=http://127.0.0.1:9999 "$image" >/dev/null
endpoint="http://$(docker port "$container" 8080/tcp)"
ready=false
for attempt in {1..30}; do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "$endpoint/healthz" || true)" = 200 ]; then
    ready=true
    break
  fi
  sleep 1
done
[ "$ready" = true ]
[ "$(curl -fsS "$endpoint/healthz")" = ok ]
for path in / /wp-admin/ /redaxo/; do
  [ "$(curl -s -o /dev/null -w '%{http_code}' "$endpoint$path")" = 403 ]
done
