#!/bin/sh

set -e

echo "Aplicando migrações do banco de dados..."

python manage.py migrate --noinput

echo "Iniciando o servidor..."

exec "$@"