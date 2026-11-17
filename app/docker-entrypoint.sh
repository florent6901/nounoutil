#!/bin/sh
set -e
ARGS="-b 0.0.0.0:8000 -w 2"
if [ "${HTTPS:-false}" = "true" ]; then
  CERT="${TLS_CERT:-/data/certs/cert.pem}"; KEY="${TLS_KEY:-/data/certs/key.pem}"
  if [ "${TLS_MODE:-selfsigned}" = "selfsigned" ]; then
    python selfsigned.py "$CERT" "$KEY"
  elif [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    echo "TLS_MODE=custom : certificat ou clé introuvable ($CERT, $KEY). Fournir les fichiers (voir README)." >&2
    exit 1
  fi
  echo "HTTPS activé (mode ${TLS_MODE:-selfsigned})"
  exec gunicorn $ARGS --certfile "$CERT" --keyfile "$KEY" app:app
fi
echo "HTTP (HTTPS désactivé)"
exec gunicorn $ARGS app:app
