FROM postgres:latest

RUN apt-get update -y; \
    apt-get install -y pgbouncer

VOLUME /etc/pgbouncer

COPY docker-entrypoint.sh /usr/local/bin/
