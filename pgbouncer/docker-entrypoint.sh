#!/bin/bash

BOUNCE_CONF=/etc/pgbouncer/pgbouncer.ini

if [ ! -f /etc/pgbouncer/hostname ]; then
    echo ${HOSTNAME} > /etc/pgbouncer/hostname

    until [ -f /etc/pgbouncer/primary ]; do
        echo "Waiting for primary to be listed in /etc/pgbouncer/primary"
        sleep 1
    done

    PRIMARY=$(cat /etc/pgbouncer/primary)

    sed -i "s/;*\* = .*/* = host=${PRIMARY}/" ${BOUNCE_CONF}
    sed -i "s/listen_addr =.*/listen_addr = 0.0.0.0/" ${BOUNCE_CONF}
    sed -i "s/listen_port =.*/listen_port = 5432/" ${BOUNCE_CONF}
    sed -i "s/;admin_users =.*/admin_users = postgres/" ${BOUNCE_CONF}

    echo '"postgres" "postgres"' > /etc/pgbouncer/userlist.txt
    chmod 600 /etc/pgbouncer/userlist.txt
fi

gosu postgres pgbouncer /etc/pgbouncer/pgbouncer.ini