# Wengertsberg pilot on mx.pdcd.net

Protected source CI remains authoritative. The publish workflow runs only after
a successful push-to-main validation from this repository, never a fork or PR.
It rebuilds and exercises the actual release images with isolated fixtures,
then publishes checksum-pinned image archives as GitHub Release assets. Those
archives contain only the public build roots and upstream images, never live
WordPress files, configuration, uploads, environment values or database data.

The `MX_GITOPS_DEPLOY_KEY` secret is a deploy key scoped only to the private
`Paul1404/web-host-gitops` repository. It pushes a manifest-only promotion branch.
That repository checks and merges the promotion; the host pulls protected main.
CI never receives the mail host's root SSH key or website runtime secrets.

Runtime configuration, Quadlet reconciliation, origin DNS, certificate renewal,
readiness, migration integrity and rollback are documented in the private
infrastructure repository. The host runs a dedicated rootless website account
with no mail privileges. Existing SMTP behavior and public website URLs remain.

During the pilot Railway services, their volumes and the site's logical
database remain preserved. Do not resume independent writes or cron on the old
copy after cutover. An origin-only rollback is safe only while data remains
identical; otherwise freeze the new copy and reverse-sync data first.

Other websites and image-based services remain on Railway. This workflow does
not migrate or deploy SVU, REDAXO, Umami or Vaultwarden.
