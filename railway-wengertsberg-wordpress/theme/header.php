<?php defined('ABSPATH') || exit; ?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip-link" href="#main">Zum Inhalt springen</a>
<header class="site-header">
    <div class="wrap header-inner">
        <?php wengertsberg_brand(); ?>
        <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav" hidden>Menü <span aria-hidden="true">☰</span></button>
        <nav id="site-nav" class="site-nav" aria-label="Hauptnavigation">
            <?php foreach (['ueber-mich' => 'Über mich', 'leistungen' => 'Leistungen', 'mein-ansatz' => 'Mein Ansatz', 'referenzen' => 'Referenzen', 'kontakt' => 'Kontakt'] as $anchor => $label): ?>
                <a <?php echo $anchor === 'kontakt' ? 'class="nav-contact"' : ''; ?> href="<?php echo esc_url(home_url('/#' . $anchor)); ?>"><?php echo esc_html($label); ?></a>
            <?php endforeach; ?>
        </nav>
    </div>
</header>
<main id="main">
