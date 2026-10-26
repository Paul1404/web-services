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

The homepage emits Open Graph metadata for link previews. `theme/share-preview.svg`
is the editable brand artwork; `share-preview.png` is its 1200x630 raster
export. Keep both in sync when changing the artwork and retain the content hash
in the public PNG filename. Verify the advertised metadata and public image
response after deployment; crawler checks do not confirm a messaging client's
actual rendering or refresh an already-cached preview.

The homepage uses standard WordPress blocks, initially seeded from
`site-content.html`. Edit the published homepage in WordPress after initial
setup. Do not import that file again over editorial changes. Existing media
stays in the media library; photography must not be committed here.

Contact details are editable under Appearance > Customize > Wengertsberg
Kontakt. The contact section retains direct email/telephone links and includes
a REST-backed contact form when SMTP is configured. The recipient comes only
from the administrator's contact setting, never from submitted form fields.

SMTP credentials are runtime references: `WENGERTSBERG_SMTP_HOST`, `_PORT`,
`_USER` and `_PASSWORD` (each with the full `WENGERTSBERG_SMTP_` prefix). Use
authenticated STARTTLS on port 587 with certificate verification enabled.
Mail is served by Stalwart on mx.pdcd.net, running Rocky Linux 10 at Contabo.
Mailcow is retired. Some website clients retain mail.pdcd.net as a compatibility
alias mapped to the container host gateway. Preserve the working SMTP hostname
and TLS verification until any endpoint change is explicitly coordinated.
Amazon SES remains available as an outbound relay. Privacy notices must account
for sender/recipient addresses and message content processed by AWS when that
relay is used. Never assume that SES is retired because Mailcow was replaced.
Keep SMTP credentials in runtime secret references and transfer them only through
secret-safe tooling. Legacy Mailcow API/CLI maintenance does not apply to Stalwart.

The form checks the request origin, validates field types/lengths and email,
uses a honeypot and short-lived signed token, and applies atomic global and
per-email rate limits. One token identifies one submission; replaying a
successful request returns its existing result without sending another mail.
Message contents are not saved in WordPress. Short-lived counters and hashed
send receipts are cleaned by an hourly WordPress cron task. Do not log request
bodies or SMTP debug output. Keep the privacy page aligned with these facts.

Verify both the browser flow and receipt in the destination mailbox. An SMTP
success response alone is not proof of delivery. Test failure responses and
duplicate requests as well as a successful send, without emailing visitors.

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

Apache listens on port 80. Keep the Railway service variable `PORT=80` so
deployment health checks target the actual listener. `/healthz` must return
200 only when WordPress can read its database. Public recovery verification
also requires HTML from the canonical website URL.

Use standard HTTP status 403 for invalid or expired contact tokens. WordPress
does not supply a status phrase for 419, which can produce HTTP 200 despite
the error response body.

## Mobile presentation

The layout changes at 800px; desktop geometry stays intact. The current
approved Sie-form copy is shared by both views in standard WordPress paragraph
blocks. Edit the published page, not the historical initial seed. Earlier
paired `desktop-copy` / `mobile-copy` passages were replaced with the shared
approved text; do not reintroduce the older informal variants.
The mobile header contact action is hidden on desktop. Below 360px it uses a
labelled envelope icon so the brand and 44px touch targets still fit.

JavaScript progressively wraps the existing qualification heading and paragraph
in a native details disclosure on mobile, restoring those original nodes on
desktop. Without JavaScript, qualifications remain expanded. Test opening and
closing with the keyboard, menu links and Escape, and resizing across 800px.
Verify at 320px and a typical phone width as well as the existing desktop view.

## Search visibility

`theme/seo.php` owns the homepage search title, description, Open Graph metadata
and one linked JSON-LD graph for WebSite, Organization, Person and WebPage.
Share title and description are intentionally separate from the search title
and description. Keep the approved social copy independent of SEO wording.
The visible homepage copy and H1 remain editorial content in WordPress. Use
only published business facts; do not fabricate reviews, opening hours or
locations. Public contact settings and the WordPress site icon supply the
organization contact details and logo. Native image blocks receive missing
width/height from their attachment metadata so optimized image URLs still
reserve their aspect ratio; keep manually supplied dimensions unchanged.

WordPress core serves `/robots.txt` and `/wp-sitemap.xml`. Keep `blog_public=1`
for this public site and unpublished legacy placeholders out of the sitemap.
Verify Googlebot-style HTTP access, canonical URL, metadata uniqueness, JSON
parsing, logo accessibility, sitemap URLs and real 404 responses after deploy.
Search Console access, sitemap submission and a recrawl request are separate
from deployment. Do not claim Google refreshed a result until it is observed;
a request does not guarantee indexing or a particular ranking/snippet.

## Editorial review view

`/?entwurf=2` is a public, noindex review route. It reads and rearranges the
published front page blocks without changing their stored content. The normal
homepage retains its existing stylesheet, markup and search/share metadata.
`design-preview.php` expects the managed group classes and falls back to the
original content when required groups are missing. Its extra CSS/JS have hashed
asset paths. The supplied Direction B desktop/mobile PDFs govern this review:
forest-green hero, sans-serif headings, gold subline and numbered sections,
two-column service cards, four reference cards, and a light form on green.
Mobile stacks the hero copy/button before a full-width portrait and places the
approach copy before its photograph. The review-only headline, subline and CTA
come from that supplied design; the existing introduction moves to About with
the headline phrase removed there to avoid repetition. The contact question
becomes its heading. Do not write those presentation changes back into the CMS.
All other editorial copy, real media and contact settings remain in WordPress.

The fixed review controls explain the ideas to Alex and switch between the
proposal and a lazily loaded same-origin comparison at `/?vergleich=1`.
Both review URLs are noindex and excluded by the actual analytics loader.
The controls also open explanatory section jumps, a real anonymized CMS case
with explicitly unanswered story questions, a neutral placeholder-logo demo
(static row or pausable band), and a labelled non-interactive consent visual.
No placeholder represents a real customer. The logo band respects reduced motion,
hover and keyboard focus; its duplicate track is hidden from assistive technology.
Neither review view starts analytics. The existing contact form keeps its real REST/SMTP flow;
reviewing the design must not send unsolicited mail. Do not fabricate logos,
client outcomes or working-session photographs to fill empty content slots.

CI uses the historical public seed only in its guarded, disposable WordPress
fixture to exercise the route, asset availability, canonical isolation and editor
content integrity. Never run that fixture against the live database.
