FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends squid && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/log/squid && touch /var/log/squid/access.log && chown -R proxy:proxy /var/log/squid
COPY squid.conf /etc/squid/squid.conf
EXPOSE 3128
# лог доступа и в файл (для make audit), и в stdout контейнера
CMD ["sh", "-c", "squid -N -f /etc/squid/squid.conf & tail -F /var/log/squid/access.log"]
