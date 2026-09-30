# Private Wengertsberg WordPress service

This Dockerfile pins the WordPress release used by this site
and ensures at build and runtime that Apache loads only `mpm_prefork`. The service has no public
Railway domain. It is reached through the project's `wengertsberg-origin`
service over the private network and uses the isolated `wengertsberg` logical
database and user on the project's MariaDB 12.3 service.

The full `/var/www/html` tree is persisted in its Railway volume. Keep the
existing table prefix and the public `https://wengertsberg.de` site
URL when migrating. Do not deploy an empty WordPress volume as a replacement
for the copied site.
