# Serviço de Autenticação com SUAP (Django API)

Este projeto é um serviço de backend construído com Django e Django REST framework que fornece autenticação de usuários utilizando o sistema SUAP do IFRN, gerando tokens JWT para acesso a APIs protegidas. A aplicação é projetada para ser executada com Docker.

## Funcionalidades Principais

- Autenticação de usuários via fluxo OAuth2 do SUAP (IFRN).
- Criação/atualização de usuários locais com base nos dados do SUAP.
- Geração de tokens de acesso e atualização JWT para autenticação em APIs.
- Endpoints protegidos para visualização de dados do usuário (`/users/me/`, `/users/<id>/`).
- Endpoint para logout (atualmente, notifica o backend; o cliente remove os tokens).

## Tecnologias Utilizadas

- **Backend:** Python, Django, Django REST framework
- **Autenticação JWT:** djangorestframework-simplejwt
- **Integração OAuth2:** SUAP (IFRN)
- **Containerização:** Docker, Docker Compose
- **Banco de Dados (Padrão de Desenvolvimento):** SQLite

## Pré-requisitos

- Docker (Engine)
- Docker Compose (geralmente vem como plugin do Docker: `docker compose`)
- Git (para clonar o repositório)

## Configuração e Instalação (Ambiente de Desenvolvimento)

1.  **Clone o Repositório:**

    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_GIT]
    cd nome-da-pasta-do-projeto-backend # Ex: auth_service_back
    ```

2.  **Crie o Arquivo de Variáveis de Ambiente (`.env`):**

    - Copie o arquivo `.env.example` para um novo arquivo chamado `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edite o arquivo `.env` e preencha todas as variáveis necessárias, como:
      - `SECRET_KEY` (gere uma chave segura)
      - `DEBUG` (True para desenvolvimento)
      - `SUAP_CLIENT_ID` (Seu Client ID do SUAP)
      - `SUAP_CLIENT_SECRET` (Seu Client Secret do SUAP)
      - `FRONTEND_APP_URL` (Ex: `http://localhost:3000`)
      - `FRONTEND_LOGIN_SUCCESS_PATH` (Ex: `/auth/handle-token`)
      - `FRONTEND_LOGIN_ERROR_PATH` (Ex: `/`)
      - `DJANGO_ALLOWED_HOSTS` (Ex: `localhost,127.0.0.1`)

3.  **Construa a Imagem e Inicie os Containers Docker:**

    ```bash
    docker compose up --build -d
    ```

    - O `-d` executa os containers em segundo plano.
    - Na primeira vez, o `--build` é importante. Depois, apenas `docker compose up -d` pode ser suficiente se o `Dockerfile` ou `requirements.txt` não mudarem.

4.  **Execute as Migrações do Banco de Dados:**
    Após os containers estarem rodando, execute as migrações do Django:

    ```bash
    docker compose exec web python manage.py migrate
    ```

    (Onde `web` é o nome do serviço do Django no seu `docker-compose.yml`).

5.  **Crie um Superusuário (Opcional):**

    ```bash
    docker compose exec web python manage.py createsuperuser
    ```

6.  **Acesse a Aplicação:**
    - O backend estará rodando em `http://localhost:8000` (ou na porta que você configurou).
    - Seu frontend Next.js (rodando separadamente em `http://localhost:3000`) poderá interagir com esta API.

## Endpoints da API (Principais)

- `GET /auth/suap/callback/`: Endpoint de callback para o SUAP (parte do fluxo OAuth2, acessado via redirecionamento do SUAP).
- `GET /api/v1/auth/users/me/`: Retorna dados do usuário autenticado. (Requer token JWT)
- `GET /api/v1/auth/users/<id>/`: Retorna dados de um usuário específico. (Requer token JWT)
- `POST /api/v1/auth/logout/`: Endpoint para o cliente notificar o logout. (Requer token JWT)

_(Para uma documentação mais detalhada da API, considere usar ferramentas como Swagger/OpenAPI e integrá-las ao seu projeto DRF)._

## Como Parar a Aplicação Dockerizada

```bash
docker compose down
```
