# Repository guidance

`AGENTS.md` is the canonical guide. `CLAUDE.md` imports it.

## Scope

This repository contains six live Railway build roots: three CMS containers
and their three protected Caddy origins. The Railway project is `web-services`.
The retired SSH host and old Compose deployment timer are not deployment
targets. Historical configuration stays in the private archived repository.

Before work, inspect status, existing changes, branch divergence, and remotes.
Read the target directory's README, Dockerfile, and entrypoint. Preserve
unrelated changes. Do not move build directories without updating Railway's
root directories and watch patterns in the same scoped operation.

## Runtime invariants

- Preserve existing volumes, logical databases, users, and website URLs.
- CMS services remain private. CloudFront uses each origin's Railway domain.
- `/healthz` is the only unauthenticated origin path. Other paths require the
  site's verification header. Never print, commit, or log its value.
- Caddy forwards the canonical Host and `X-Forwarded-Proto: https`.
- Apache runs prefork only. Build and startup both defend against event MPM.
- REDAXO must refuse an empty migrated configuration; its migration hold is
  only for an explicitly authorized data transfer.
- Never commit credentials, website uploads, database dumps, or runtime config.
- Umami, Vaultwarden, MariaDB, and PostgreSQL are Railway image sources, not
  deployments controlled by this repository's Dockerfiles.

## Verification

CI builds all six Dockerfiles and smoke-tests protected origins. For changes
to origin routing, test health, denial without the header, and public website
responses. Run `sh -n` on POSIX entrypoints and `bash -n` on REDAXO's entrypoint.
Use `node --test tests/*.test.mjs` for the redirect function.

Production completion requires an explicit terminal Railway deployment state
and independent endpoint readback. State when authenticated CMS, backup, or
restore checks were not performed. Never infer that Git contains runtime data.

Dependency updates are reviewed. Keep Caddy and WordPress versions aligned
within their respective groups. Do not add unrelated services or restore old
Compose automation as cleanup.
