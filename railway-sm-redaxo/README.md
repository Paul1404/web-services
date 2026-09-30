# Private Schlossmuehle REDAXO service

This service pins an immutable Friends Of REDAXO image digest. It has no public Railway domain. The
protected `sm-redaxo-origin` service reaches it over the private network.
The image and runtime explicitly disable Apache's event MPM so only the
PHP-compatible prefork MPM is active.

REDAXO persists all of `/var/www/html` in a Railway volume. The database is an isolated logical database and user on
the project's shared MariaDB 12.3 service.

`REDAXO_MIGRATION_HOLD=1` runs an idle process so the volume can be populated
without installing a blank site. After the files and database are copied,
set it to `0`. The entrypoint refuses an empty volume and uses REDAXO's own
`db:set-connection` command to update the copied config with the Railway
database settings before starting Apache. Never print or commit database
credentials. For recovery, restore verified website-file and database backups,
then verify a full restart and the protected origin before directing traffic.
The former SSH host is retired and is not a recovery target.
