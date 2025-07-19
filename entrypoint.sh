echo "Aplicando migrações do banco de dados..."
python manage.py migrate --no-input

# --- SEÇÃO DE CRIAÇÃO AUTOMÁTICA DE ORGANIZADORES ---
echo "Verificando organizadores iniciais..."
if [ -n "$INITIAL_CAMPUS_CODES" ]; then
  for CAMPUS_CODE in $(echo $INITIAL_CAMPUS_CODES | sed "s/,/ /g")
  do
    echo "Provisionando organizador para o campus: $CAMPUS_CODE"
    
    # Converte para minúsculo
    LOWER_CAMPUS_CODE=$(echo "$CAMPUS_CODE" | tr '[:upper:]' '[:lower:]')
    
    python manage.py create_organizer \
      --campus=$CAMPUS_CODE \
      --email="organizador.${LOWER_CAMPUS_CODE}@ifrn.edu.br" \
      --password="$DEFAULT_ORGANIZER_PASS"
  done
else
  echo "Nenhum campus inicial para provisionar."
fi

exec "$@"