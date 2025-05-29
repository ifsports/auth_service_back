# Dockerfile (Versão Simplificada e Corrigida)

# 1. Imagem base Python oficial
FROM python:3.10-slim-bullseye

# 2. Definir variáveis de ambiente (formato corrigido e combinado)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Definir o diretório de trabalho dentro do container
WORKDIR /app

# 4. Copiar o arquivo de dependências e instalar
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante do código do projeto
COPY . /app/

# 6. Expor a porta que a aplicação usará dentro do container
EXPOSE 8000

# 7. Comando para rodar a aplicação (servidor de desenvolvimento do Django)
# Para um setup de desenvolvimento. Migrações podem ser rodadas manualmente
# ou através de um entrypoint script / docker-compose mais elaborado.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]