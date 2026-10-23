#!/bin/sh
set -eu

# The build validates prefork, but the Railway runtime can expose event again.
# Enforce one MPM immediately before the upstream WordPress entrypoint runs.
if [ -e /etc/apache2/mods-enabled/mpm_event.load ]; then
    a2dismod mpm_event >/dev/null
fi

# WordPress lives on a volume. Keep the versioned theme in sync without
# replacing uploads, database content, other themes, or site configuration.
mkdir -p /var/www/html/wp-content/themes/wengertsberg
cp -R /usr/src/wengertsberg-theme/. /var/www/html/wp-content/themes/wengertsberg/
chown -R www-data:www-data /var/www/html/wp-content/themes/wengertsberg

exec docker-entrypoint.sh "$@"
