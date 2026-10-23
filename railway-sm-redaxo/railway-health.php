<?php
// Check migrated files and the configured database without booting site code.
ini_set('display_errors', '0');
$ready = false;
ob_start();
register_shutdown_function(static function () use (&$ready): void {
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    http_response_code($ready ? 200 : 503);
    header('Content-Type: text/plain; charset=utf-8');
    header('Cache-Control: no-store');
    echo $ready ? 'ok' : 'unavailable';
});

try {
    $config = __DIR__ . '/redaxo/data/core/config.yml';
    if (!is_file(__DIR__ . '/index.php') || !is_file($config) || filesize($config) === 0) {
        exit;
    }
    $host = parse_url('mysql://' . getenv('REDAXO_DB_HOST'));
    if (!$host || !isset($host['host'])) {
        exit;
    }
    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
    $connection = mysqli_init();
    $connection->options(MYSQLI_OPT_CONNECT_TIMEOUT, 3);
    $connection->real_connect(
        trim($host['host'], '[]'),
        getenv('REDAXO_DB_LOGIN'),
        getenv('REDAXO_DB_PASSWORD'),
        getenv('REDAXO_DB_NAME'),
        $host['port'] ?? 3306
    );
    // Respect custom REDAXO prefixes without exposing any table or row data.
    $tables = $connection->query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND (table_name LIKE '%article' OR table_name LIKE '%user')")->fetch_row();
    $ready = (int) $tables[0] >= 2;
    $connection->close();
} catch (Throwable $error) {
    // Health responses must never contain configuration or database details.
}
