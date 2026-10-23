#!/usr/bin/env python3
"""Production-image checks on disposable, private Docker resources only."""
import http.cookiejar
import json
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITES = {
    'svu': ('sv-untereuerheim.de', 'X-SVU-Origin-Key'),
    'wengertsberg': ('wengertsberg.de', 'X-Wengertsberg-Origin-Key'),
    'sm-redaxo': ('schlossmuehle-untereuerheim.de', 'X-SM-Origin-Key'),
}
directory, image = sys.argv[1:]
site = next((name for name in SITES if directory in (
    f'railway-{name}-origin', f'railway-{name}-wordpress', 'railway-sm-redaxo' if name == 'sm-redaxo' else '',
)), None)
assert site, 'Unknown build directory'
prefix = 'web-services-release-' + uuid.uuid4().hex[:10]
containers, volumes = [], []
network = prefix + '-network'


def docker(*args, check=True):
    result = subprocess.run(['docker', *args], capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def container(role, *args, selected_image=image, command=(), entrypoint=None):
    name = prefix + '-' + role
    containers.append(name)
    options = ['run', '-d', '--name', name, '--network', network]
    if entrypoint:
        options += ['--entrypoint', entrypoint]
    docker(*options, *args, selected_image, *command)
    return name


def free_port():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        return connection.getsockname()[1]


class LocalRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, target):
        expected, actual = urllib.parse.urlsplit(request.full_url), urllib.parse.urlsplit(target)
        assert actual.netloc == expected.netloc and actual.scheme == 'http', 'Fixture tried a non-local redirect'
        return super().redirect_request(request, fp, code, message, headers, target)


cookies = http.cookiejar.CookieJar()
http = urllib.request.build_opener(LocalRedirect(), urllib.request.HTTPCookieProcessor(cookies))


def request(base, path='/', headers=None, data=None):
    assert urllib.parse.urlsplit(base).hostname == '127.0.0.1', 'Only local test endpoints are allowed'
    try:
        response = http.open(urllib.request.Request(base + path, headers=headers or {}, data=data), timeout=8)
    except urllib.error.HTTPError as error:
        response = error
    return response.code, response.headers, response.read()


def wait_for(base, path, status=200, attempts=60):
    last = None
    for _ in range(attempts):
        try:
            last = request(base, path)
            if last[0] == status:
                return last
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise AssertionError(f'{path} did not reach {status}; last status: {last[0] if last else "unreachable"}')


def origin_checks():
    fixture = ROOT / 'tests/fixtures/upstream.mjs'
    upstream = container('upstream', '-v', f'{fixture}:/fixture.mjs:ro',
                         selected_image='node:24-alpine', command=('node', '/fixture.mjs'))
    port = free_port()
    container('origin', '-p', f'127.0.0.1:{port}:8080', '-e', 'ORIGIN_VERIFY=release-fixture-key',
              '-e', f'WORDPRESS_UPSTREAM=http://{upstream}:9000',
              '-e', f'REDAXO_UPSTREAM=http://{upstream}:9000')
    base = f'http://127.0.0.1:{port}'
    assert wait_for(base, '/healthz')[2] == b'ok'
    host, header = SITES[site]
    for path in ['/', '/wp-admin/', '/redaxo/', '/railway-health.php', '/healthz/']:
        assert request(base, path)[0] == 403, path
        assert request(base, path, {header: 'wrong'})[0] == 403, path
    status, _, body = request(base, '/fixture?check=1', {header: 'release-fixture-key'})
    assert status == 200
    assert json.loads(body) == {'path': '/fixture?check=1', 'host': host, 'protocol': 'https'}
    docker('stop', upstream)
    assert request(base, '/healthz')[0] >= 500, 'Origin health ignored a failed upstream'
    docker('start', upstream)
    assert wait_for(base, '/healthz')[2] == b'ok'
    missing = docker('run', '--rm', '--network', network, '-e', 'WORDPRESS_UPSTREAM=http://unused',
                     '-e', 'REDAXO_UPSTREAM=http://unused', image, 'true', check=False)
    assert missing.returncode != 0, 'Origin started without its verification key'
    print(f'{directory}: health, authorized proxy headers, denial, upstream failure and recovery passed')


def cms_checks():
    port = free_port()
    base = f'http://127.0.0.1:{port}'
    volume = prefix + '-site'
    database_volume = prefix + '-database'
    volumes.extend([volume, database_volume])
    docker('volume', 'create', volume)
    docker('volume', 'create', database_volume)
    database = container('db', '--network-alias', 'release-db',
                         '-e', 'MARIADB_ROOT_PASSWORD=release-root-password',
                         '-e', 'MARIADB_DATABASE=release', '-e', 'MARIADB_USER=release',
                         '-e', 'MARIADB_PASSWORD=release-fixture-password',
                         '-v', f'{database_volume}:/var/lib/mysql', selected_image='mariadb:12.3')
    for _ in range(60):
        if docker('exec', database, 'healthcheck.sh', '--connect', '--innodb_initialized', check=False).returncode == 0:
            break
        time.sleep(1)
    else:
        raise AssertionError('Disposable database did not become ready')
    mount = ['-v', f'{volume}:/var/www/html']
    if site == 'sm-redaxo':
        empty = docker('run', '--rm', '--network', network, image, 'true', check=False)
        assert empty.returncode != 0 and 'refusing a fresh install' in empty.stderr
        environment = ['-e', 'REDAXO_DB_HOST=release-db', '-e', 'REDAXO_DB_NAME=release',
                       '-e', 'REDAXO_DB_LOGIN=release', '-e', 'REDAXO_DB_PASSWORD=release-fixture-password',
                       '-e', f'REDAXO_SERVER={base}', '-e', 'REDAXO_SERVERNAME=Release fixture',
                       '-e', 'REDAXO_ERROR_EMAIL=release@example.invalid', '-e', 'REDAXO_LANG=en_gb',
                       '-e', 'REDAXO_TIMEZONE=Europe/Berlin', '-e', 'REDAXO_DB_CHARSET=utf8mb4',
                       '-e', 'REDAXO_ADMIN_USER=release-admin', '-e', 'REDAXO_ADMIN_PASSWORD=release-fixture-password']
        # Test-only upstream setup on a newly created volume and an internal network.
        docker('run', '--rm', '--network', network, *mount, *environment,
               '--entrypoint', 'docker-entrypoint.sh', image, 'true')
        cms = container('cms', '-p', f'127.0.0.1:{port}:80', *mount, *environment)
        assert wait_for(base, '/railway-health.php')[2] == b'ok'
        assert request(base, '/redaxo/index.php')[0] == 200, 'REDAXO backend did not boot'
    else:
        fixture = ROOT / 'tests/fixtures/wordpress.php'
        cms = container('cms', '-p', f'127.0.0.1:{port}:80', *mount,
                        '-v', f'{fixture}:/release-fixture.php:ro',
                        '-e', 'WORDPRESS_DB_HOST=release-db', '-e', 'WORDPRESS_DB_NAME=release',
                        '-e', 'WORDPRESS_DB_USER=release', '-e', 'WORDPRESS_DB_PASSWORD=release-fixture-password',
                        '-e', 'WEB_SERVICES_RELEASE_TEST=1', '-e', f'RELEASE_URL={base}',
                        '-e', f'RELEASE_THEME={site}')
        wait_for(base, '/wp-admin/install.php')
        assert request(base, '/railway-health.php')[0] == 503, 'An uninstalled WordPress reported ready'
        docker('exec', cms, 'php', '/release-fixture.php')
        assert wait_for(base, '/railway-health.php')[2] == b'ok'
        assert b'Release fixture content' in request(base)[2]
        request(base, '/wp-login.php')
        login = urllib.parse.urlencode({'log': 'release-admin', 'pwd': 'release-fixture-password',
                                       'redirect_to': base + '/wp-admin/', 'testcookie': '1'}).encode()
        status, _, body = request(base, '/wp-login.php', data=login)
        assert status == 200 and b'wpbody-content' in body, 'WordPress editor login failed'
        if site == 'wengertsberg':
            status, _, body = request(base)
            for filename in ['style.css', 'site.js', 'share-preview.png']:
                digest = docker('exec', cms, 'php', '-r',
                                f'echo substr(hash_file("sha256", "/var/www/html/wp-content/themes/wengertsberg/{filename}"),0,12);').stdout
                stem, extension = filename.rsplit('.', 1)
                asset = f'/wp-content/themes/wengertsberg/assets/{stem}.{digest}.{extension}'
                assert request(base, asset)[0] == 200, asset
    modules = docker('exec', cms, 'apache2ctl', '-M').stdout
    assert 'mpm_prefork_module' in modules and 'mpm_event_module' not in modules
    docker('exec', cms, 'sh', '-c', 'mkdir -p /var/www/html/release-sentinel; echo fixture > /var/www/html/release-sentinel/preserved.txt')
    docker('restart', cms)
    assert wait_for(base, '/railway-health.php')[2] == b'ok'
    assert request(base, '/release-sentinel/preserved.txt')[2].strip() == b'fixture'
    if site != 'sm-redaxo':
        assert b'Release fixture content' in request(base)[2], 'Restart lost editor content'
    docker('stop', database)
    status, _, body = request(base, '/railway-health.php')
    assert status == 503 and body == b'unavailable', 'Health did not safely reject an unavailable database'
    docker('start', database)
    assert wait_for(base, '/railway-health.php')[2] == b'ok'
    print(f'{directory}: CMS/database readiness, prefork, persistent files, database failure and recovery passed')


try:
    docker('network', 'create', '--internal', network)
    if directory.endswith('-origin'):
        origin_checks()
    else:
        cms_checks()
except Exception:
    for name in containers:
        print(docker('logs', '--tail', '30', name, check=False).stdout, file=sys.stderr)
    raise
finally:
    for name in reversed(containers):
        docker('rm', '-f', '-v', name, check=False)
    for name in volumes:
        docker('volume', 'rm', name, check=False)
    docker('network', 'rm', network, check=False)
