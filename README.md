# Web services

The CMS recipes, Wengertsberg theme and tests have moved to
[vertex-images](https://github.com/Paul1404/vertex-images/tree/main/recipes/web-services).
Make future changes there. The publishers here are disabled and their Fleet
secret has been removed. This repository retains source history and recovery
archives pending archival.

## Historical sources

| Website | Build directory | Application |
| --- | --- | --- |
| SV Untereuerheim | `railway-svu-wordpress/` | WordPress |
| Schlossmühle Untereuerheim | `railway-sm-redaxo/` | REDAXO |
| Wengertsberg | `railway-wengertsberg-wordpress/` | WordPress |

The `railway-*` paths predate the Vertex migration. The three corresponding
`railway-*-origin/` directories contain Caddy recipes and tests; active routing
uses the Vertex Gateway. The old `web-compose-projects` and `web-host-gitops`
repositories are also archived.

Traffic follows this path:

```text
Browser -> CloudFront -> protected Vertex Gateway -> CMS -> MariaDB
                                                     |
                                                     +-> persistent volume
```

Private `vertex-fleet` owns deployment configuration. The Gateway checks the
origin header and forwards the canonical Host and HTTPS scheme. Keep header
values secret. Each CMS exposes a database-backed `/healthz` through
`railway-health.php`.

WordPress and REDAXO persist `/var/www/html`. Preserve site data, database users
and public URLs. Do not replace a populated volume or run competing writers.
REDAXO refuses to start without its migrated configuration. Read [AGENTS.md](AGENTS.md)
and the context README before using these recovery sources.

## Checks

CI retains the source and six image checks. The fixtures cover origin headers
and denial, database readiness and failure, restart persistence, Apache setup
and WordPress editor login.

```sh
python3 tests/release-smoke.py <build-directory> <image>
```

Fixtures use disposable Docker resources and synthetic data. Never point them
at production storage or credentials. After a deployment, check Fleet, public
HTTPS and the protected origin. Test authenticated CMS flows when affected.

Original source rights and upstream dependency licenses still apply.
