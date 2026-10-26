<?php
defined('ABSPATH') || exit;

function wengertsberg_design_preview(): bool {
    return is_front_page() && isset($_GET['entwurf']) && is_string($_GET['entwurf']) && $_GET['entwurf'] === '2';
}

add_filter('body_class', function ($classes) {
    if (wengertsberg_design_preview()) $classes[] = 'design-preview';
    return $classes;
});
add_filter('wp_robots', function ($robots) {
    $comparison = is_front_page() && isset($_GET['vergleich']) && is_string($_GET['vergleich']) && $_GET['vergleich'] === '1';
    if (wengertsberg_design_preview() || $comparison) {
        unset($robots['index']);
        $robots['noindex'] = true;
    }
    return $robots;
});
add_action('wp_enqueue_scripts', function () {
    if (!wengertsberg_design_preview()) return;
    wp_enqueue_style('wengertsberg-design-preview', get_template_directory_uri() . '/' . wengertsberg_asset('design-preview.css'), ['wengertsberg'], null);
    wp_enqueue_script('wengertsberg-design-preview', get_template_directory_uri() . '/' . wengertsberg_asset('design-preview.js'), ['wengertsberg'], null, true);
});

function wengertsberg_preview_find(array $blocks, string $class): ?array {
    foreach ($blocks as $block) {
        $classes = preg_split('/\s+/', $block['attrs']['className'] ?? '');
        if (in_array($class, $classes, true)) return $block;
        $found = wengertsberg_preview_find($block['innerBlocks'] ?? [], $class);
        if ($found) return $found;
    }
    return null;
}
function wengertsberg_preview_render(array $blocks): string {
    return implode("\n", array_map(fn($block) => do_shortcode(shortcode_unautop(render_block($block))), $blocks));
}
function wengertsberg_preview_heading(array $blocks): array {
    foreach ($blocks as $block) {
        if ($block['blockName'] === 'core/heading') return $block;
    }
    return [];
}

// Rearrange the published blocks for review. No seed import, copied editorial
// text, database write, invented testimonial, customer logo or new media asset.
add_filter('the_content', function ($content) {
    if (!wengertsberg_design_preview() || !in_the_loop() || !is_main_query()) return $content;
    $post = get_post();
    if (!$post || $post->post_status !== 'publish') return $content;
    $blocks = parse_blocks($post->post_content);
    $groups = [];
    foreach (['hero-copy', 'hero-portrait', 'about-copy', 'about-place', 'services', 'service-list', 'approach-copy', 'approach-photo', 'reference-intro', 'reference-list', 'contact-copy', 'contact-details'] as $class) {
        $groups[$class] = wengertsberg_preview_find($blocks, $class);
        if (!$groups[$class]) return $content;
    }
    $hero = $groups['hero-copy']['innerBlocks'];
    $kicker = wengertsberg_preview_find($hero, 'intro-label');
    $description = wengertsberg_preview_find($hero, 'hero-description');
    $location = wengertsberg_preview_find($hero, 'hero-location');
    $heading = wengertsberg_preview_heading($hero);
    if (!$kicker || !$description || !$location || !$heading) return $content;
    $description_html = wengertsberg_preview_render([$description]);
    $description_html = str_replace('vom Shopfloor bis in die Vorstandsetage', '<strong class="preview-emphasis">vom Shopfloor bis in die Vorstandsetage</strong>', $description_html);
    $button = array_values(array_filter($hero, fn($b) => $b['blockName'] === 'core/html'));
    $about_heading = wengertsberg_preview_heading($groups['about-copy']['innerBlocks']);
    $about_body = array_values(array_filter($groups['about-copy']['innerBlocks'], fn($b) => $b !== $about_heading));
    $service_children = $groups['services']['innerBlocks'][0]['innerBlocks'] ?? [];
    $service_intro = array_values(array_filter($service_children, fn($b) => $b['blockName'] !== 'core/group'));
    $approach = $groups['approach-copy']['innerBlocks'];
    $approach_heading = wengertsberg_preview_heading($approach);
    $approach_paragraphs = array_values(array_filter($approach, fn($b) => $b['blockName'] === 'core/paragraph'));
    if (!$about_heading || count($service_intro) < 2 || count($approach_paragraphs) !== 2) return $content;
    $case_example = '';
    foreach ($groups['reference-list']['innerBlocks'] as $reference) {
        $rendered_reference = wengertsberg_preview_render([$reference]);
        if (str_contains(wp_strip_all_tags($rendered_reference), 'Workshop in Lissabon')) {
            $case_example = $rendered_reference;
            break;
        }
    }
    ob_start(); ?>
    <aside class="preview-reviewbar" aria-label="Entwurf und Ideen für Alex">
        <div class="wrap preview-reviewbar-inner">
            <div class="preview-review-intro"><strong>Für Alex: Entwurf und Ideen</strong><p>Ansichten und neue Bausteine ausprobieren.</p></div>
            <div class="preview-review-controls">
                <div class="preview-view-switch" role="group" aria-label="Websiteansicht">
                    <button type="button" data-review-view="design" aria-pressed="true" aria-controls="preview-design-panel">Unser Vorschlag</button>
                    <button type="button" data-review-view="original" aria-pressed="false" aria-controls="preview-original-panel">Bisherige Website</button>
                </div>
                <nav class="preview-review-ideas" aria-label="Ideen ansehen"><button type="button" data-preview-notes>Änderungen</button><button type="button" data-preview-cases>Kunden &amp; Logos</button><button type="button" data-preview-consent>Analysehinweis</button></nav>
            </div>
        </div>
    </aside>
    <section id="preview-original-panel" class="preview-original-panel" hidden aria-label="Bisherige Website zum Vergleich"><iframe title="Bisherige Wengertsberg Website" data-original-src="<?php echo esc_url(add_query_arg('vergleich', '1', home_url('/'))); ?>" referrerpolicy="no-referrer"></iframe></section>
    <div id="preview-design-panel">
    <section class="preview-hero" aria-label="Alexander Eckert">
        <div class="wrap preview-hero-grid">
            <div class="preview-kicker"><?php echo wengertsberg_preview_render([$kicker]); ?></div>
            <div class="preview-hero-title"><?php echo wengertsberg_preview_render([$heading]); ?></div>
            <div class="preview-portrait"><?php echo wengertsberg_preview_render([$groups['hero-portrait']]); ?></div>
            <div class="preview-introduction"><?php echo $description_html . wengertsberg_preview_render($button) . wengertsberg_preview_render([$location]); ?></div>
        </div>
    </section>
    <section id="ueber-mich" class="preview-about section">
        <div class="wrap preview-about-grid">
            <div class="preview-section-heading"><p class="preview-eyebrow">Industriepraxis und Ehrenamt</p><?php echo wengertsberg_preview_render([$about_heading]); ?></div>
            <div class="about-copy"><?php echo wengertsberg_preview_render($about_body); ?></div>
        </div>
    </section>
    <section id="leistungen" class="preview-services section">
        <div class="wrap preview-services-grid"><div class="preview-section-heading"><?php echo wengertsberg_preview_render($service_intro); ?></div><?php echo wengertsberg_preview_render([$groups['service-list']]); ?></div>
    </section>
    <section id="mein-ansatz" class="preview-approach section">
        <div class="wrap"><?php echo wengertsberg_preview_render([$approach_heading]); ?><div class="preview-approach-lead"><?php echo wengertsberg_preview_render([$approach_paragraphs[0]]); ?></div>
            <div class="preview-approach-story"><?php echo wengertsberg_preview_render([$groups['approach-photo']]); ?><div class="preview-approach-text"><?php echo wengertsberg_preview_render([$approach_paragraphs[1]]); ?></div></div>
        </div>
    </section>
    <section id="referenzen" class="preview-references section"><div class="wrap preview-reference-grid"><?php echo wengertsberg_preview_render([$groups['reference-intro'], $groups['reference-list']]); ?></div></section>
    <section id="kontakt" class="contact section"><div class="wrap contact-grid"><?php echo wengertsberg_preview_render([$groups['contact-copy'], $groups['contact-details']]); ?><div class="preview-contact-place"><?php echo wengertsberg_preview_render([$groups['about-place']]); ?></div></div></section>
    </div>
    <dialog class="preview-dialog" id="preview-notes" aria-labelledby="preview-notes-title">
        <button class="preview-dialog-close" type="button" data-close-preview aria-label="Hinweise schließen">×</button>
        <h2 id="preview-notes-title">Was wir ändern würden</h2>
        <p>Der Entwurf zeigt, wie Alex und seine Erfahrung stärker sichtbar werden können. Die freigegebenen Texte und vorhandenen Fotos bleiben die Grundlage.</p>
        <div class="preview-change-list">
            <div><h3>Alex früher und größer zeigen</h3><p>Das Porträt steht direkt am Einstieg. Die Passage vom Shopfloor bis in die Vorstandsetage bekommt mehr Gewicht.</p><button type="button" data-review-jump="#main">Einstieg ansehen</button></div>
            <div><h3>Industriepraxis und Ehrenamt hervorheben</h3><p>Die Erfahrung aus Betrieb und Verein wird in einem eigenen Abschnitt zusammengeführt.</p><button type="button" data-review-jump="#ueber-mich">Abschnitt ansehen</button></div>
            <div><h3>Leistungen leichter überblicken</h3><p>Ruhige Zeilen und eine klarere Gewichtung ersetzen das wiederholte Kartenraster.</p><button type="button" data-review-jump="#leistungen">Leistungen ansehen</button></div>
            <div><h3>Kundenarbeit greifbar machen</h3><p>Kundengeschichten und Firmenlogos kommen mit echten Inhalten und Freigaben dazu. Der nächste Button zeigt den möglichen Aufbau.</p><button type="button" data-open-cases>Kundengeschichten und Logos ansehen</button></div>
        </div>
    </dialog>
    <dialog class="preview-dialog preview-cases-dialog" id="preview-cases" aria-labelledby="preview-cases-title">
        <button class="preview-dialog-close" type="button" data-close-preview aria-label="Kundenbeispiele schließen">×</button>
        <p class="preview-example-label">Bausteine zum Ausprobieren</p><h2 id="preview-cases-title">Kundengeschichten und Firmenlogos</h2>
        <p>So könnten wir die Arbeit konkreter zeigen. Namen, Logos, Zitate und Ergebnisse werden erst nach Freigabe veröffentlicht.</p>
        <article class="preview-case-example"><p class="preview-example-label">Beispielaufbau einer Kundengeschichte</p>
            <?php echo $case_example ?: '<h3>Eine Kundengeschichte</h3>'; ?>
            <dl><dt>Ausgangssituation</dt><dd>Welche Frage oder Herausforderung hatte das Team? Von Alex zu ergänzen.</dd><dt>Alex’ Beitrag</dt><dd>Was hat Alex konzipiert, moderiert oder begleitet? Das konkrete Vorgehen ergänzen.</dd><dt>Ergebnis</dt><dd>Was wurde erreicht oder geklärt? Nur belegbare und freigegebene Aussagen aufnehmen.</dd><dt>Kundenname und Zitat</dt><dd>Nach Freigabe nennen. Bei einem Einsatz über andere Auftraggeber Alex’ Rolle deutlich machen.</dd></dl>
        </article>
        <h3 class="preview-logo-heading">So könnten die Logos erscheinen</h3><p>Die Felder unten sind ausdrücklich Platzhalter und stehen für keine tatsächlichen Kunden.</p>
        <div class="preview-logo-options" role="group" aria-label="Logodarstellung"><button type="button" data-logo-mode="row" aria-pressed="true">Ruhige Reihe</button><button type="button" data-logo-mode="band" aria-pressed="false">Langsam laufendes Band</button></div>
        <div class="preview-logo-demo" data-logo-demo data-mode="row" data-paused="false" tabindex="0" role="region" aria-label="Logobeispiel mit Platzhaltern">
            <div class="preview-logo-track"><?php for ($copy = 0; $copy < 2; $copy++): ?><div class="preview-logo-group" <?php echo $copy ? 'aria-hidden="true"' : ''; ?>><?php for ($slot = 0; $slot < 6; $slot++): ?><div class="preview-logo-placeholder">Firmenlogo</div><?php endfor; ?></div><?php endfor; ?></div>
        </div>
        <button type="button" class="preview-logo-pause" data-logo-pause aria-pressed="false" hidden>Bewegung pausieren</button>
        <p class="preview-example-note">Bei wenigen Logos passt die ruhige Reihe. Bei ausreichend freigegebenen Logos kann das Band eingesetzt werden. Es pausiert bei Berührung mit dem Mauszeiger oder Tastaturfokus und bleibt bei reduzierter Bewegung statisch.</p>
        <p>Für die nächste Fassung brauchen wir zwei bis drei freigegebene Kundengeschichten und die zugehörigen Logodateien. Echte Fotos aus Workshops oder Gesprächen können die vorhandenen Bilder ergänzen.</p>
    </dialog>
    <dialog class="preview-dialog preview-consent-dialog" id="preview-consent" aria-labelledby="preview-consent-title">
        <button class="preview-dialog-close" type="button" data-close-preview aria-label="Beispiel schließen">×</button>
        <p class="preview-example-label">Gestaltungsbeispiel</p><h2 id="preview-consent-title">Darf ich diese Website auswerten?</h2>
        <p>Mit Ihrer Erlaubnis zähle ich Besuche und schaue mir stichprobenartig an, wie die Seite genutzt wird, zum Beispiel Klicks und Scrollbewegungen. Formulare werden dabei nicht aufgezeichnet. Die Website funktioniert auch, wenn Sie ablehnen.</p>
        <div class="preview-choice-example"><button type="button" disabled>Erlauben</button><button type="button" disabled>Ablehnen</button></div>
        <a href="<?php echo esc_url(home_url('/datenschutzerklaerung/')); ?>">Mehr dazu in der Datenschutzerklärung</a>
        <p class="preview-example-note">Im Entwurf wird keine Analyse gestartet. Die Auswahl oben zeigt nur die Gestaltung.</p>
    </dialog>
    <?php
    return wp_filter_content_tags(ob_get_clean(), 'the_content');
}, 20);
