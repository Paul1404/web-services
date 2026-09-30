FROM wordpress:7.1.0

# The amd64 image can enable both Apache MPMs; PHP needs prefork only.
RUN a2dismod mpm_event \
    && a2enmod mpm_prefork \
    && apache2ctl -t

COPY entrypoint.sh /usr/local/bin/svu-wordpress-entrypoint
RUN chmod 755 /usr/local/bin/svu-wordpress-entrypoint

ENTRYPOINT ["svu-wordpress-entrypoint"]
CMD ["apache2-foreground"]
