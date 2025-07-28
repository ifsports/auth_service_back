#!/bin/sh

echo "Aplicando migrações do banco de dados..."
python manage.py migrate --no-input

# Este único comando agora cria TODOS os organizadores de uma vez
echo "Criando organizadores iniciais..."
python manage.py create_organizer

# Inicia o servidor web
exec "$@"