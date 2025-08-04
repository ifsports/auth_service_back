from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
import requests
from urllib.parse import quote
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer

from messaging import send_audit_log, build_log_payload

from concurrent.futures import ThreadPoolExecutor

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

SUAP_TOKEN_URL = "https://suap.ifrn.edu.br/o/token/"
SUAP_API_EU_URL = "https://suap.ifrn.edu.br/api/rh/eu"
SUAP_API_MEUS_DADOS_URL = "https://suap.ifrn.edu.br/api/v2/minhas-informacoes/meus-dados/"


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    access_token = refresh.access_token

    access_token['matricula'] = user.matricula
    access_token['nome'] = user.nome
    access_token['campus'] = user.campus
    access_token['groups'] = [group.name for group in user.groups.all()]
    access_token['iss'] = 'ifsports-recomeco'

    return {
        'refresh': str(refresh),
        'access': str(access_token),
    }


@extend_schema(exclude=True)
def suap_oauth_callback_view(request):
    code = request.GET.get("code")
    frontend_url_base = getattr(
        settings, "FRONTEND_APP_URL", "http://localhost:3000")
    frontend_success_path = getattr(
        settings, "FRONTEND_LOGIN_SUCCESS_PATH", "/auth/handle-token")

    request_data_token = {
        "grant_type": "authorization_code", "code": code,
        "client_id": settings.SUAP_CLIENT_ID, "client_secret": settings.SUAP_CLIENT_SECRET,
        "scope": "identificacao email documentos_pessoais",
    }
    suap_token_response = requests.post(
        SUAP_TOKEN_URL, data=request_data_token, timeout=15)
    suap_token_response.raise_for_status()
    suap_token_data = suap_token_response.json()
    access_token_suap = suap_token_data.get("access_token")
    headers_suap_api = {"Authorization": f"Bearer {access_token_suap}"}

    data_suap = {}
    data_eu = {}
    with ThreadPoolExecutor() as executor:
        future_meus_dados = executor.submit(
            requests.get, SUAP_API_MEUS_DADOS_URL, headers=headers_suap_api, timeout=10)
        future_eu = executor.submit(
            requests.get, SUAP_API_EU_URL, headers=headers_suap_api, timeout=10)

        try:
            response_meus_dados = future_meus_dados.result()
            if response_meus_dados.status_code == 200:
                data_suap = response_meus_dados.json()
        except Exception as e:
            print(f"AVISO: Falha ao buscar dados da API MEUS_DADOS: {e}")

        try:
            response_eu = future_eu.result()
            if response_eu.status_code == 200:
                data_eu = response_eu.json()
        except Exception as e:
            print(f"AVISO: Falha ao buscar dados da API EU: {e}")

    matricula_suap = data_suap.get('matricula')
    if not matricula_suap:
        return HttpResponseRedirect(f"{frontend_url_base}/login?error=falha_suap")

    vinculo_data = data_suap.get('vinculo', {})

    email_suap = (
        data_eu.get('email_google_classroom')
        or data_eu.get('email')
        or data_eu.get('email_preferencial')
        or data_eu.get('email_academico')
        or data_eu.get('email_secundario')
    )

    if not email_suap:
        return HttpResponseRedirect(f"{frontend_url_base}/login?error=email_nao_encontrado")

    user_defaults = {
        'email': email_suap,
        'nome': data_suap.get('nome_usual'),
        'campus': vinculo_data.get('campus'),
        'foto': data_suap.get('url_foto_75x100', ''),
        'sexo': data_eu.get('sexo'),
        'tipo_usuario': data_suap.get('tipo_vinculo'),
        'curso': vinculo_data.get('curso'),
        'situacao': vinculo_data.get('situacao'),
        'data_nascimento': data_suap.get('data_nascimento'),
    }

    user, created = User.objects.update_or_create(
        matricula=matricula_suap, defaults=user_defaults)

    if not user.groups.exists():
        try:
            jogador_group = Group.objects.get(name='Jogador')
            user.groups.add(jogador_group)
        except Group.DoesNotExist:
            print("AVISO: O grupo 'Jogador' não foi encontrado.")

    app_tokens = get_tokens_for_user(user)
    nome_formatado = quote(user_defaults.get('nome') or '')
    email_formatado = quote(user_defaults.get('email') or '')
    foto_formatada = quote(user_defaults.get('foto') or '')
    redirect_url = (
        f"{frontend_url_base}{frontend_success_path}"
        f"?token={app_tokens['access']}&refresh_token={app_tokens['refresh']}"
        f"&user_created={str(created).lower()}&userId={matricula_suap}"
        f"&userName={nome_formatado}&userEmail={email_formatado}"
        f"&userImage={foto_formatada}"
    )

    log_payload = build_log_payload(
        request=request,
        user=user,
        event_type="auth.login",
        operation_type="LOGIN",
        new_data={
            "message": f"Usuário {user.nome} ({user.matricula}) logou com sucesso via SUAP."}
    )
    send_audit_log(log_payload)

    return HttpResponseRedirect(redirect_url)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticação"],
        summary="Autentica um organizador via matrícula e senha.",
        description="""
Autentica um usuário (geralmente um organizador) com base na matrícula e senha locais.

**Exemplo de Corpo da Requisição (Payload):**

.. code-block:: json

   {
     "matricula": "20210000000001",
     "password": "senha_forte_123"
   }

**Exemplo de Resposta de Sucesso:**

.. code-block:: json

   {
     "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
""",
        responses={
            200: OpenApiResponse(description="Autenticação bem-sucedida. Retorna os tokens."),
            401: OpenApiResponse(description="Credenciais inválidas."),
            403: OpenApiResponse(description="Esta conta está desativada.")
        }
    )
    def post(self, request, *args, **kwargs):
        matricula = request.data.get('matricula')
        password = request.data.get('password')
        user = authenticate(username=matricula, password=password)

        if user and user.is_active:
            tokens = get_tokens_for_user(user)

            log_payload = build_log_payload(
                request=request,
                user=user,
                event_type="auth.login",
                operation_type="LOGIN",
                new_data={
                    "message": f"Organizador {user.nome} logou com sucesso."}
            )

            send_audit_log(log_payload)

            return Response(tokens, status=status.HTTP_200_OK)

        elif user and not user.is_active:
            return Response(
                {"error": "Esta conta está desativada."},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            return Response(
                {"error": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Autenticação"],
        summary="Registra o evento de logout do usuário.",
        description="""
Este endpoint apenas registra a intenção de logout para fins de auditoria.
O cliente (frontend) é responsável por apagar os tokens armazenados localmente para efetivar o logout.

**Esta rota não recebe corpo na requisição.**
""",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Logout recebido. O cliente deve apagar os tokens.",
                examples=[
                    OpenApiExample('Exemplo de Resposta', value={
                                   'detail': 'Logout recebido. O cliente deve invalidar/remover os tokens JWT.'})
                ]
            ),
            401: OpenApiResponse(description="Não autenticado.")
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        log_payload = build_log_payload(
            request=request,
            user=user,
            event_type="auth.logout",
            operation_type="LOGOUT",
            new_data={"message": f"Usuário {user.nome} solicitou logout."}
        )
        send_audit_log(log_payload)
        return Response({"detail": "Logout recebido. O cliente deve invalidar/remover os tokens JWT."}, status=status.HTTP_200_OK)


class ValidateUsersByMatriculaView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Usuários"],
        summary="Verifica a existência de usuários por matrícula.",
        description="""
Recebe uma lista de matrículas e retorna quais são válidas e quais são inválidas.

**Exemplo de Corpo da Requisição (Payload):**

.. code-block:: json

   {
     "user_ids": ["20210001", "20210002", "matricula_invalida"]
   }

**Exemplo de Resposta:**

.. code-block:: json

   {
     "all_exist": false,
     "message": "As seguintes matrículas não foram encontradas: matricula_invalida",
     "valid_ids": ["20210001", "20210002"],
     "invalid_ids": ["matricula_invalida"]
   }
""",
        responses={
            200: OpenApiResponse(description="Validação concluída."),
            400: OpenApiResponse(description="Erro no formato da requisição.")
        }
    )
    def post(self, request, *args, **kwargs):
        matriculas_para_validar = request.data.get('user_ids', [])

        if not isinstance(matriculas_para_validar, list):
            return Response(
                {"error": "Entrada inválida. 'user_ids' (contendo matrículas) deve ser uma lista."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            matriculas_para_validar_str = [
                str(m) for m in matriculas_para_validar]
        except ValueError:
            return Response(
                {"error": "Formato de matrícula inválido. Todas as matrículas devem ser conversíveis para string."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not matriculas_para_validar_str:
            return Response(
                {"all_exist": True, "message": "Nenhuma matrícula fornecida para validação.", "valid_ids": [],
                 "invalid_ids": []},
                status=status.HTTP_200_OK
            )

        usuarios_existentes_qs = User.objects.filter(
            matricula__in=matriculas_para_validar_str)

        matriculas_existentes_no_db = set(
            user.matricula for user in usuarios_existentes_qs)

        matriculas_solicitadas_set = set(matriculas_para_validar_str)

        matriculas_invalidas = list(
            matriculas_solicitadas_set - matriculas_existentes_no_db)

        matriculas_validas = list(
            matriculas_existentes_no_db.intersection(matriculas_solicitadas_set))

        if not matriculas_invalidas:
            return Response({
                "all_exist": True,
                "message": "Todas as matrículas fornecidas são válidas.",
                "valid_ids": matriculas_validas,
                "invalid_ids": []
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "all_exist": False,
                "message": f"As seguintes matrículas não foram encontradas: {', '.join(matriculas_invalidas)}",
                "valid_ids": matriculas_validas,
                "invalid_ids": matriculas_invalidas
            }, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Usuários"],
        summary="Retorna os dados do usuário atualmente autenticado.",
        description="""
Utiliza o token de autenticação enviado no header para identificar o usuário.

**Exemplo de Resposta de Sucesso:**

.. code-block:: json

   {
     "id": "1",
     "matricula": "20221094040022",
     "email": "usuario@exemplo.com",
     "nome": "Nome do Usuário",
     "campus": "CN",
     "foto": "https://url.da.foto/imagem.png",
     "sexo": "M",
     "tipo_usuario": "ALUNO",
     "curso": "Técnico em Informática",
     "situacao": "Matriculado",
     "data_nascimento": "2005-10-20",
     "is_active": true,
     "is_staff": false,
     "groups": ["Jogador"]
   }
""",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Não autenticado.")
        }
    )
    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Usuários"],
        summary="Busca os dados de um usuário específico por matrícula.",
        description="""
Note que o `id` na URL corresponde à `matrícula` do usuário.

**Exemplo de Resposta de Sucesso:**

.. code-block:: json

   {
     "id": "a1b2c3d4...",
     "matricula": "20210002",
     "email": "outro@exemplo.com",
     "nome": "Outro Usuário",
     "campus": "PF",
     "foto": "https://url.da.foto/outra.png",
     "sexo": "F",
     "tipo_usuario": "SERVIDOR",
     "curso": null,
     "situacao": "Ativo",
     "data_nascimento": "1990-05-15",
     "is_active": true,
     "is_staff": true,
     "groups": ["Organizador"]
   }
""",
        responses={
            200: UserSerializer,
            404: OpenApiResponse(description="Usuário com a matrícula especificada não foi encontrado.")
        }
    )
    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, matricula=id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UsersByIdView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Usuários"],
        summary="Busca múltiplos usuários por uma lista de matrículas.",
        description="""
Recebe uma lista de matrículas e retorna uma lista com os dados dos usuários encontrados.

**Exemplo de Corpo da Requisição (Payload):**

.. code-block:: json

   {
     "ids": ["20210001", "20210002"]
   }
""",
        responses={
            200: UserSerializer(many=True),
            400: OpenApiResponse(description="Corpo da requisição inválido ou ausente.")
        }
    )
    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not ids:
            return Response({
                "detail": "Uma lista de IDs é obrigatória."
            }, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(matricula__in=ids)
        serializer = UserSerializer(users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
