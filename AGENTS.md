# Repository guidance

`AGENTS.md` is the canonical guide. `CLAUDE.md` imports it.

## Scope

This repository contains six build roots: three CMS containers and their three
protected Caddy origins. Production runs on mx.pdcd.net through the private
web-host-gitops repository. The Railway web-services project is stopped as a
cold data fallback; never reconnect or redeploy it during normal releases.
The retired SSH host and old Compose deployment timer are not deployment
targets. Historical configuration stays in the private archived repository.

The explicitly authorized Wengertsberg pilot uses a new pull deployment on
mx.pdcd.net, separate from the retired host/timer. Its desired state and host
runbook live in private Paul1404/web-host-gitops. See docs/wengertsberg-gitops.md.
Keep Railway's services, volumes and database as a preserved fallback throughout
pilot verification. Never switch back to stale data after the new site accepts
writes. Other services retain their existing Railway deployment path.

Before work, inspect status, existing changes, branch divergence, and remotes.
Read the target directory's README, Dockerfile, and entrypoint. Preserve
unrelated changes. Do not move build directories without updating Railway's
root directories and watch patterns in the same scoped operation.

## Runtime invariants

- Preserve existing volumes, logical databases, users, and website URLs.
- CMS services remain private. CloudFront uses each origin's Railway domain.
- `/healthz` is the only unauthenticated origin path. Other paths require the
  site's verification header. Never print, commit, or log its value.
- Origin `/healthz` proxies the private CMS `/railway-health.php` probe. A
  healthy Caddy process alone is insufficient. The probe returns only `ok` or
  `unavailable`, disables caching, and makes read-only database checks.
- Railway deployment health paths are `/healthz` for all six services, with a
  90-second startup timeout. CMS Apache aliases that path to the probe file.
- Set Railway `PORT=80` on the CMS services and `PORT=8080` on origins, matching
  their actual Apache/Caddy listeners. Private upstreams still use CMS port 80;
  do not change those listeners to accommodate an injected health-check port.
- Origin readiness depends on its CMS. Recover the CMS first, then retry an
  origin deployment that failed while its backend was unavailable.
- Entrypoints refresh only the service-owned `railway-health.php` in the
  persistent web root. Do not replace CMS configuration, media or editor content.
- Caddy forwards the canonical Host and `X-Forwarded-Proto: https`.
- Apache runs prefork only. Build and startup both defend against event MPM.
- REDAXO must refuse an empty migrated configuration; its migration hold is
  only for an explicitly authorized data transfer.
- Never commit credentials, website uploads, database dumps, or runtime config.
- Wengertsberg's managed theme is in `railway-wengertsberg-wordpress/theme/`.
  Its entrypoint syncs theme files into the persistent volume, but must never
  replace WordPress page content. Read that directory's README before edits.
- Umami, Vaultwarden, MariaDB, and PostgreSQL are Railway image sources, not
  deployments controlled by this repository's Dockerfiles.

## Verification

CI builds and exercises all six Dockerfiles with `python3 tests/release-smoke.py
<build-directory> <image>`. Fixtures create uniquely named Docker networks and
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

Production completion requires an explicit terminal Railway deployment state
and independent endpoint readback. State when authenticated CMS, backup, or
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
