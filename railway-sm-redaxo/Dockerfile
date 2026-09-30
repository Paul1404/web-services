FROM friendsofredaxo/redaxo@sha256:212699c8ec07f5e7bd9d8f52458a919671450627f77e2165e805f057b67f767c

# PHP uses prefork; loading the event MPM as well prevents Apache starting.
RUN a2dismod mpm_event \
    && a2enmod mpm_prefork \
    && apache2ctl -t

COPY entrypoint.sh /usr/local/bin/redaxo-railway-entrypoint
RUN chmod 755 /usr/local/bin/redaxo-railway-entrypoint

ENTRYPOINT ["/usr/local/bin/redaxo-railway-entrypoint"]
CMD ["apache2-foreground"]
