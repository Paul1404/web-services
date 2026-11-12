# Web services

Active image recipes, the managed theme and tests have moved to
[vertex-images](https://github.com/Paul1404/vertex-images/tree/main/recipes/web-services).
The three sites now use its tested, scanned and signed images through private
Vertex Fleet promotion. Make future changes in that repository. The publishers
here are disabled; do not re-enable them. This repository remains available for
historical source and recovery archives pending the archival decision.

The sections below describe the previous build and release setup.

Build and release sources for three websites running on the Vertex RKE2 cluster:
SV Untereuerheim, Schlossmühle Untereuerheim and Wengertsberg. Their CMS images
are published to GHCR and deployed through Rancher Fleet. Existing public
domains continue through CloudFront to protected Vertex Gateway routes.

This repository contains build sources and release automation, not live website
files, database contents, credentials or runtime configuration. The private
Vertex Fleet repository owns the Kubernetes desired state.

## Website builds

| Website | Build directory | Application |
| --- | --- | --- |
| SV Untereuerheim | `railway-svu-wordpress/` | WordPress |
| Schlossmühle Untereuerheim | `railway-sm-redaxo/` | REDAXO |
| Wengertsberg | `railway-wengertsberg-wordpress/` | WordPress |

The `railway-*` names are historical paths still used by the Dockerfiles, CI
and release scripts. They do not describe the active hosting platform. The
three corresponding `railway-*-origin/` directories contain historical Caddy
origin builds and supporting sources. Active website routing uses the Vertex
Gateway rather than those per-site proxy containers.

```text
Browser -> CloudFront -> protected Vertex Gateway -> CMS service -> MariaDB
                                                       |
                                                       +-> persistent volume
```

The Gateway enforces each site's origin verification header and forwards the
canonical host and HTTPS scheme. Never print, commit or log header values.
The CMS images provide a database-backed `/healthz` check through the
service-owned `railway-health.php` file; that filename is retained for
compatibility.

## Release and operation

A successful push-to-main validation triggers the site publishers. When a
site's release inputs changed, they build and exercise its application image,
publish a checked immutable image and promote its digest and release metadata
to the private Vertex Fleet repository. Fleet reconciles that desired state.
The publishers use a scoped deploy key and do not receive website runtime
credentials or host SSH access.

Each CMS and database has its own Kubernetes workload and persistent storage.
Preserve the existing public URLs, database users and site data. WordPress and
REDAXO persist `/var/www/html`; never replace a populated volume with an empty
one or run independent writers against the same data. REDAXO refuses an empty
migrated installation. Consult the build directory's README before changing it.

Umami and Vaultwarden run separately on Vertex using upstream images. Their
releases are not built by the website publishers in this repository.

## Maintenance and verification

- Dependabot reviews the Dockerfiles and GitHub Actions weekly. Related Caddy
  and WordPress updates are grouped.
- CI builds and exercises the site images. Origin tests cover forwarding,
  direct-request denial and upstream failure; CMS fixtures cover database-backed
  readiness, persistence and Apache configuration. WordPress also exercises an
  editor login.
- `python3 tests/release-smoke.py <build-directory> <image>` uses isolated Docker
  resources and synthetic data, without production credentials or volumes.
- After a production change, verify the checked release, Fleet reconciliation,
  canonical HTTPS and protected-origin behavior. Test authenticated CMS flows
  when relevant.

## Historical configuration

The old Railway and single-host deployment descriptions are historical. The
former private `web-compose-projects` and `web-host-gitops` repositories are
archived. They are not the active website deployment path.

## Source availability

The repository is public for inspection. Publication does not change ownership
or grant an additional license to the original deployment code. Upstream images
and dependencies retain their respective licenses.
