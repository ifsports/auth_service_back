from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
import requests
from django.contrib.auth.models import Group

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer

# URLs do SUAP
SUAP_TOKEN_URL = "https://suap.ifrn.edu.br/o/token/"
SUAP_API_EU_URL = "https://suap.ifrn.edu.br/api/eu"
SUAP_API_MEUS_DADOS_URL = "https://suap.ifrn.edu.br/api/edu/meus-dados-aluno"

# Função auxiliar para gerar tokens JWT para o usuário


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# --- VIEW DE CALLBACK SUAP  ---
def suap_oauth_callback_view(request):
    code = request.GET.get("code")
    frontend_url_base = getattr(
        settings, "FRONTEND_APP_URL", "http://localhost:3000")
    frontend_success_path = getattr(
        settings, "FRONTEND_LOGIN_SUCCESS_PATH", "/auth/handle-token")

    # Assume que SUAP_CLIENT_ID e SUAP_CLIENT_SECRET estão configurados
    suap_client_id = settings.SUAP_CLIENT_ID
    suap_client_secret = settings.SUAP_CLIENT_SECRET

    request_data_token = {
        "grant_type": "authorization_code",
        "code": code,  # Assume que 'code' sempre estará presente
        "client_id": suap_client_id,
        "client_secret": suap_client_secret,
        "scope": "identificacao email documentos_pessoais",
    }

    suap_token_response = requests.post(
        SUAP_TOKEN_URL, data=request_data_token, timeout=15)
    suap_token_response.raise_for_status()  # Levanta exceção para erros HTTP
    suap_token_data = suap_token_response.json()

    access_token_suap = suap_token_data.get("access_token")
    print(f'TOKEN TOKEN TOKEN TOKEN TOKEN TOKEN{access_token_suap}')

    headers_suap_api = {"Authorization": f"Bearer {access_token_suap}"}

    # Obter dados do usuário do SUAP
    response_eu = requests.get(
        SUAP_API_EU_URL, headers=headers_suap_api, timeout=10)
    response_eu.raise_for_status()
    data_eu = response_eu.json()

    # response_meus_dados = requests.get(
    #     SUAP_API_MEUS_DADOS_URL, headers=headers_suap_api, timeout=10)
    # response_meus_dados.raise_for_status()
    # data_meus_dados = response_meus_dados.json()

    # Preparar dados e criar/atualizar usuário local
    email_suap = (data_eu.get('email_google_classroom') or data_eu.get(
        'email_academico') or data_eu.get('email_pessoal') or data_eu.get('email'))
    nome_suap = (data_eu.get('nome_usual') or data_eu.get(
        'nome_social') or data_eu.get('nome') or data_eu.get('nome_registro'))
    matricula_suap = data_eu.get('identificacao')

    user_defaults = {
        'email': email_suap,
        'nome': nome_suap,
        'campus': data_eu.get('campus'),
        'foto': data_eu.get('foto'),
        'sexo': data_eu.get('sexo', ''),
        'tipo_usuario': data_eu.get('tipo_usuario'),
        # 'curso': data_meus_dados.get('curso'),
        # 'situacao': data_meus_dados.get('situacao'),
        'data_nascimento': data_eu.get('data_de_nascimento'),
    }

    # Cria ou atualiza o usuário.
    user, created = User.objects.update_or_create(
        matricula=matricula_suap, defaults=user_defaults)

    try:
        # Garante que o usuário seja adicionado ao grupo "Jogador"
        # se ele não pertencer a nenhum grupo ainda (caso de um novo usuário)
        # ou se ele não for um Organizador.
        if not user.groups.exists():
            jogador_group = Group.objects.get(name='Jogador')
            user.groups.add(jogador_group)
            print(f"Usuário {user.matricula} adicionado ao grupo 'Jogador'.")
    except Group.DoesNotExist:
        # Isso só deve acontecer se a migração não tiver sido executada
        print("AVISO: O grupo 'Jogador' não foi encontrado. Execute as migrações.")

    action_msg = "criado" if created else "atualizado"
    print(
        f"Usuário {user.matricula} ({user.nome}) {action_msg} com sucesso via callback SUAP.")

    # Gerar token JWT da sua aplicação para o usuário
    app_tokens = get_tokens_for_user(user)
    app_access_token = app_tokens['access']
    app_refresh_token = app_tokens.get('refresh')

    # Redirecionar para o frontend com o token JWT da sua aplicação
    redirect_to_frontend_url = f"{frontend_url_base}{frontend_success_path}?token={app_access_token}"
    if app_refresh_token:
        redirect_to_frontend_url += f"&refresh_token={app_refresh_token}"
    redirect_to_frontend_url += f"&user_created={str(created).lower()}"

    print(f"Redirecionando para o frontend: {redirect_to_frontend_url}")
    return HttpResponseRedirect(redirect_to_frontend_url)


# --- OUTRAS API VIEWS (Logout, UserMe, UserDetail) ---
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Lógica de logout (ex: blacklist de token se implementado)
        print(
            f"Usuário {request.user.matricula} solicitou logout. O cliente deve remover os tokens.")
        return Response({"detail": "Logout recebido. O cliente deve invalidar/remover os tokens JWT."}, status=status.HTTP_200_OK)


class ValidateUsersByMatriculaView(APIView):
    permission_classes = [AllowAny]

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

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
