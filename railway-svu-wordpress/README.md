# Private SVU WordPress service

This service runs WordPress 7.1.0 on Railway without a public domain. Apache
uses the prefork MPM at build and runtime. The protected `svu-origin` service
proxies to it over Railway's private network.

WordPress uses the isolated `svu` database and login on the `web-services`
project's MariaDB 12.3 service. Keep the existing table prefix and
`https://sv-untereuerheim.de` site URL. The full `/var/www/html` tree lives
on a persistent Railway volume; do not replace it with an empty volume.
