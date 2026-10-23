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

## Website theme

`theme/` is the managed Wengertsberg classic theme. The image stores it outside
the WordPress volume; the entrypoint copies it into `wp-content/themes/wengertsberg`
on startup. Deploy theme changes through this build root. Theme deployment
does not activate the theme or replace database content.

`build-theme-assets.sh` generates CSS and JavaScript filenames containing
their content hash during the image build. Use these paths instead of query
parameters so browser/CDN caching cannot retain a previous design. Run the
same script when applying theme files directly for an initial setup.

The homepage uses standard WordPress blocks, initially seeded from
`site-content.html`. Edit the published homepage in WordPress after initial
setup. Do not import that file again over editorial changes. Existing media
stays in the media library; photography must not be committed here.

Contact details are editable under Appearance > Customize > Wengertsberg
Kontakt. The contact section uses email and telephone links. No contact
submissions are stored. A future server-side form needs verified delivery,
abuse protection, and corresponding privacy text.

Use `php -l theme/*.php` (one file per invocation), `node --check theme/site.js`,
and `sh -n entrypoint.sh` for scoped source checks. Exercise anchor navigation,
the mobile menu, legal pages, and contact behavior in a real browser after
deployment. Back up database and existing theme/media files outside Git before
changing the active theme or front-page option. Restoring only an image does
not restore WordPress options or page content.

Keep the minimal `theme.json`: it enables the current core Group layout
markup in this classic theme. Without it, WordPress adds a legacy inner
container and the site's grids no longer receive their intended children.
The theme sets the default block gap to zero and owns its section spacing.

When retiring Elementor, deactivate it in a separate request before changing
site options from a PHP maintenance script. Already-loaded Elementor option
hooks remain registered for that request. Set an authorized WordPress user
before importing trusted block markup so core does not strip the theme's
inline SVG icons. Public pages must not use decorative dot separators or
em/en dashes. Avoid generic feature-card grids, qualification badges, repeated
category labels, and inflated marketing copy. Keep the focus on Alexander,
his actual experience, and readable service descriptions.
