#!/bin/sh
set -eu

# Railway can expose the event MPM again when mounting the runtime volume.
if [ -e /etc/apache2/mods-enabled/mpm_event.load ]; then
    a2dismod mpm_event >/dev/null
fi

exec docker-entrypoint.sh "$@"
