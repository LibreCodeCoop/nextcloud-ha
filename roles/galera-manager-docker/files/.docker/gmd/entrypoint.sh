#!/bin/sh
set -e -u

if [ "$1" = 'gmd' ]; then
  set +e
  if [ -z "${ADMIN_USER}" ]; then
    ADMIN_USER=admin
  fi
  if [ -z "${ADMIN_PASSWORD}" ]; then
    ADMIN_PASSWORD=admin
  fi
  OUTPUT=$(gmd db init --admin-user-name=${ADMIN_USER} --admin-password=${ADMIN_PASSWORD} 2>&1)
  RETVAL=$?
  set -e

  if [ "$OUTPUT" = "Database already initialized, use --force flag to reinit it" ]; then
    echo "Starting..."
  else
    if [ $RETVAL -ne 0 ]; then
      echo "$OUTPUT"
      exit $RETVAL
    fi

    echo "Generating JWT RSA signing key"
    if [ ! -e /var/lib/gmd/jwt-rsa.key ]; then
      ssh-keygen -f /var/lib/gmd/jwt-rsa.key -m PEM -t rsa -b 2048 -q -N ""
    fi
    echo "All done. Starting..."
  fi

fi

RSA_PRIVATE_KEY=/var/lib/gmd/jwt-rsa.key exec "$@"
