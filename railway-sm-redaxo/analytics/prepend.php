<?php
// Public HTML only; no CMS backend, API, file or readiness instrumentation.
$path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
if (PHP_SAPI === 'cli' || preg_match('~^/(redaxo|api|railway-health\.php|healthz)(/|$)~', $path)) return;
ob_start(function ($html) {
    if (stripos($html, '</body>') === false) return $html;
    $html = preg_replace('~<script\b[^>]*src=["\']https://umami\.pdcd\.net/(?:script|recorder)\.js[^"\']*["\'][^>]*>.*?</script>~is', '', $html);
    return str_ireplace('</body>', '<script defer src="/site-analytics/consent.js" data-website-id="2e537260-7c47-486c-8af2-3b6e77657582" data-hosts="schlossmuehle-untereuerheim.de,www.schlossmuehle-untereuerheim.de" data-article-ids="true" data-privacy="/index.php?article_id=8"></script></body>', $html);
});
