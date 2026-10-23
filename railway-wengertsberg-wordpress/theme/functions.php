<?php
defined('ABSPATH') || exit;

add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('responsive-embeds');
    add_theme_support('editor-styles');
    add_editor_style(wengertsberg_asset('style.css'));
    add_theme_support('html5', ['search-form', 'gallery', 'caption', 'style', 'script']);
});

function wengertsberg_asset(string $file): string {
    $digest = substr(hash_file('sha256', get_template_directory() . '/' . $file), 0, 12);
    $parts = pathinfo($file);
    return 'assets/' . $parts['filename'] . '.' . $digest . '.' . $parts['extension'];
}

add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('wengertsberg', get_template_directory_uri() . '/' . wengertsberg_asset('style.css'), [], null);
    wp_enqueue_script('wengertsberg', get_template_directory_uri() . '/' . wengertsberg_asset('site.js'), [], null, true);
});

// This site uses local system fonts and local photography only.
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');
add_filter('wp_resource_hints', function ($urls, $relation) {
    return $relation === 'dns-prefetch' ? array_filter($urls, fn($url) => !str_contains(is_array($url) ? $url['href'] : $url, 's.w.org')) : $urls;
}, 10, 2);

function wengertsberg_brand(): void {
    echo '<a class="brand" href="' . esc_url(home_url('/')) . '" aria-label="Wengertsberg, zur Startseite"><span class="brand-letter" aria-hidden="true">W</span><span class="brand-name">WENGERTSBERG<span class="brand-subtitle">TRAINING &amp; CONSULTING</span></span></a>';
}

add_action('wp_head', function () {
    if (is_front_page()) {
        echo '<meta name="description" content="Alexander Eckert begleitet Führungskräfte, Teams und Organisationen durch Veränderung. Coaching, Training und Consulting aus der Region Schweinfurt.">' . "\n";
    }
});

add_filter('document_title_separator', fn() => '|');
add_filter('pre_get_document_title', function ($title) {
    return is_front_page() ? 'Wengertsberg Training und Consulting' : $title;
});

add_action('customize_register', function ($customizer) {
    $customizer->add_section('wengertsberg_contact', ['title' => 'Wengertsberg Kontakt']);
    $customizer->add_setting('wengertsberg_email', ['default' => '', 'sanitize_callback' => 'sanitize_email']);
    $customizer->add_control('wengertsberg_email', ['label' => 'Geschäftliche E-Mail-Adresse', 'section' => 'wengertsberg_contact', 'type' => 'email']);
    $customizer->add_setting('wengertsberg_phone', ['default' => '', 'sanitize_callback' => 'sanitize_text_field']);
    $customizer->add_control('wengertsberg_phone', ['label' => 'Geschäftliche Telefonnummer', 'section' => 'wengertsberg_contact', 'type' => 'text']);
});

add_shortcode('wengertsberg_contact', function () {
    $email = sanitize_email(get_theme_mod('wengertsberg_email', ''));
    $phone = sanitize_text_field(get_theme_mod('wengertsberg_phone', ''));
    $html = '';
    if ($email) {
        $html .= '<a class="contact-address" href="' . esc_url('mailto:' . $email) . '">' . esc_html($email) . '</a>';
    }
    if ($phone) {
        $html .= '<p class="contact-phone"><a href="' . esc_url('tel:' . preg_replace('/[^+0-9]/', '', $phone)) . '">' . esc_html($phone) . '</a></p>';
    }
    return $html . '<p class="contact-place">Region Schweinfurt in Bayern</p>';
});
