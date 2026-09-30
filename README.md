# Web services

Deployment sources for three websites hosted on Railway: SV Untereuerheim,
Schlossmühle Untereuerheim, and Wengertsberg. Each website has a private CMS
container and a small Caddy origin proxy used by its existing CloudFront
distribution.

This repository contains deployment code and documentation only. Website files,
databases, credentials, and backups live outside Git.

## Services

| Railway service | Build directory | Purpose |
| --- | --- | --- |
| `svu-wp` | `railway-svu-wordpress/` | WordPress for SV Untereuerheim |
| `svu-origin` | `railway-svu-origin/` | Protected origin proxy |
| `sm-redaxo` | `railway-sm-redaxo/` | REDAXO for Schlossmühle |
| `sm-redaxo-origin` | `railway-sm-redaxo-origin/` | Protected origin proxy and redirect function source |
| `wengertsberg-wp` | `railway-wengertsberg-wordpress/` | WordPress for Wengertsberg |
| `wengertsberg-origin` | `railway-wengertsberg-origin/` | Protected origin proxy |

```text
Browser -> CloudFront -> Caddy origin -> private CMS -> private MariaDB
                                         |
                                         +-> persistent website volume
```

Each origin exposes `/healthz` without authentication. Other requests require
the site's CloudFront origin verification header. The CMS services have no
public Railway domain. The origins forward the canonical hostname and HTTPS
indication to avoid redirect loops.

## Deployment

The Railway project is `web-services`. Each of the six build services follows
this repository's `main` branch, uses its own directory as the build root, and
builds that directory's Dockerfile. Watch patterns should match only that
directory, so documentation changes do not redeploy websites.

Service variables, persistent volumes, database users, domains, and CloudFront
configuration are managed separately. Source changes must preserve those
resources. Consult the directory's README before changing a service.

WordPress and REDAXO persist `/var/www/html`. Never replace a populated volume
with an empty one or run two writable instances against the same site data.
REDAXO's startup checks refuse an empty migrated installation.

## Image-based services

Umami, Vaultwarden, MariaDB, and PostgreSQL also run in the Railway project,
using Docker image sources rather than builds from this repository. Updating
a Dockerfile here does not update those services. Their image versions and
backups must be inspected and maintained directly in Railway.

## Maintenance and verification

- Dependabot checks the six active Dockerfiles and GitHub Actions weekly.
  Related Caddy and WordPress updates are grouped; upgrades remain reviewed.
- CI builds all six images on Linux. Origin checks validate Caddy, public health
  responses, and rejection of direct requests without the verification header.
- After a production change, verify the actual Railway deployment and public
  website. Test an authenticated CMS workflow when relevant.
- Railway volume snapshots are not an independent off-platform backup.
  Recovery also needs database exports and website-file backups. This repo
  does not contain them or claim they have been verified.

## Historical configuration

The former private `web-compose-projects` repository is retained as historical
material. Its SSH host has been retired. Its Compose stacks, systemd deployment
timer, and host-based rollback instructions are not an active deployment path.
This public repository starts with fresh history and only the current Railway
build sources. No old host configuration or runtime data has been imported.

## Source availability

The repository is public for inspection. Publication does not change ownership
or grant an additional license to the original deployment code. Upstream images
and dependencies retain their respective licenses.
