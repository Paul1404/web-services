FROM wordpress:7.1.0

# The amd64 variant currently enables both Apache MPMs. PHP's prefork MPM is
# required; loading event alongside it makes Apache fail before WordPress starts.
RUN a2dismod mpm_event \
    && a2enmod mpm_prefork \
    && apache2ctl -t

COPY entrypoint.sh /usr/local/bin/wengertsberg-entrypoint
RUN chmod 755 /usr/local/bin/wengertsberg-entrypoint

ENTRYPOINT ["wengertsberg-entrypoint"]
CMD ["apache2-foreground"]
