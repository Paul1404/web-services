#!/bin/sh
set -eu

# Railway can expose the event MPM again when mounting the runtime volume.
if [ -e /etc/apache2/mods-enabled/mpm_event.load ]; then
    a2dismod mpm_event >/dev/null
fi

# The web root is persistent; refresh only this service-owned readiness probe.
cp /usr/local/share/railway-health.php /var/www/html/railway-health.php
chmod 644 /var/www/html/railway-health.php

exec docker-entrypoint.sh "$@"
