# Repository guidance

`AGENTS.md` is the canonical guide. `CLAUDE.md` imports it.

## Scope

Website releases are promoted to the private `Paul1404/vertex-fleet`
repository using the scoped `VERTEX_FLEET_DEPLOY_KEY`. The three CMS sites run
on the Vertex RKE2 cluster. The old mx application workloads and volumes have been retired;
`web-host-gitops` is archived.

This repository contains three CMS build roots and three historical protected
Caddy origin build roots. Current public traffic uses CloudFront and protected
Vertex Gateway routes. Railway-era configuration is historical and is not the active deployment path.
Never reconnect or redeploy a stale copy during normal releases.

Before work, inspect status, existing changes, branch divergence, and remotes.
Read the target directory's README, Dockerfile, and entrypoint. Preserve
unrelated changes. Do not rename historical build directories without updating their CI, release
scripts and consumers in the same scoped operation.

## Runtime invariants

- Preserve existing volumes, logical databases, users, and website URLs.
- CMS services remain private in their per-site Kubernetes networks. CloudFront
  reaches the protected Vertex origins configured in vertex-fleet.
- Vertex origin routes require the site verification header. Never print,
  commit, or log its value.
- CMS Apache aliases `/healthz` to the private `/railway-health.php` probe.
  It returns only `ok` or `unavailable`, disables caching, and makes read-only
  database checks. The historical Caddy origin proxies that check; Caddy alone
  is not sufficient to establish backend readiness.
- The CMS and historical origin images listen on ports 80 and 8080 respectively.
  Preserve their Apache/Caddy listener contracts when changing builds.
- Entrypoints refresh only the service-owned `railway-health.php` in the
  persistent web root. Do not replace CMS configuration, media or editor content.
- The Vertex ingress forwards the canonical Host and `X-Forwarded-Proto: https`.
- Apache runs prefork only. Build and startup both defend against event MPM.
- REDAXO must refuse an empty migrated configuration; its migration hold is
  only for an explicitly authorized data transfer.
- Never commit credentials, website uploads, database dumps, or runtime config.
- Wengertsberg's managed theme is in `railway-wengertsberg-wordpress/theme/`.
  Its entrypoint syncs theme files into the persistent volume, but must never
  replace WordPress page content. Read that directory's README before edits.
- Umami and Vaultwarden use digest-pinned upstream images managed separately
  by Vertex Fleet; the website publishers do not deploy them.

## Verification

CI builds and exercises application images with `python3 tests/release-smoke.py
<build-directory> <image>`. The three required origin check contexts remain,
but build and exercise an origin only when its image or shared smoke inputs
change. Fixtures create uniquely named Docker networks and
volumes, have no external network access, and are removed afterward. Never use
production volumes, databases or credentials in these tests. WordPress fixture
mail is disabled. REDAXO fresh setup is test-only; production still refuses an
empty migrated site.

Origin tests cover valid forwarding, canonical Host/HTTPS headers, invalid
tokens, failed upstreams and recovery. CMS tests use MariaDB 12.3 and verify
readiness, restart persistence, prefork-only Apache and safe database failure
responses. WordPress additionally verifies an editor login and managed theme
asset URLs. REDAXO verifies migrated startup and the backend login page.

For changes
to origin routing, test health, denial without the header, and public website
responses. Run `sh -n` on POSIX entrypoints and `bash -n` on REDAXO's entrypoint.
Use `node --test tests/*.test.mjs` for the redirect function.

Production completion requires successful source checks and publication, a
checked desired-state promotion, successful Fleet reconciliation, and independent
canonical HTTPS and protected-origin readiness/denial readback. Do not restart
legacy deployments to satisfy an obsolete check. State when authenticated CMS, backup, or
restore checks were not performed. Never infer that Git contains runtime data.

Dependency updates are reviewed. Keep Caddy and WordPress versions aligned
within their respective groups. Do not add unrelated services or restore old
Compose automation as cleanup.

`main` requires an up-to-date pull request with secret scanning, source checks
and all six image checks passing. Apply these requirements to administrators
as well; no second-person approval is required. Do not bypass protection to
ship changes.

SVU and Schlossmuehle also publish checked immutable archives through
`publish-websites.yml`. Release jobs have no host SSH or runtime credentials.
Keep source runtime volumes and the migration write fences intact as fallbacks.
When a site's Fleet origin deployment has been retired, publish only its tested
application image and preserve the last origin and database artifact metadata.
Restoring an origin deployment makes its next release build and verify that
origin again.

## Optional analytics

Each CMS build owns analytics/consent.js and its integration. Keep the three
loader copies identical. The WordPress MU plugin replaces legacy direct Umami
script tags only in public HTML and excludes logged-in users. REDAXO uses its native OUTPUT_FILTER extension in the owned web_analytics
addon, preserving persisted templates and content. Its frontend consumes PHP
output buffers, so auto_prepend_file buffering cannot protect real REDAXO pages.
The image test must exercise rex_response::sendPage, not a plain PHP echo.
Analysis and recording require an explicit choice; the loader honors withdrawal,
DNT and GPC. Strict masking and form exclusions are server-side Umami settings.
A recorder script's data-mask-level attributes do not configure this version.
Do not expose authenticated pages or record the Kontor2 membership form.
Privacy pages are CMS data; snapshot and update them separately from images.
