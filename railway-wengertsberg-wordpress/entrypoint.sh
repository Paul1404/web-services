#!/bin/sh
set -eu

# The build validates prefork, but the Railway runtime can expose event again.
# Enforce one MPM immediately before the upstream WordPress entrypoint runs.
if [ -e /etc/apache2/mods-enabled/mpm_event.load ]; then
    a2dismod mpm_event >/dev/null
fi

exec docker-entrypoint.sh "$@"
