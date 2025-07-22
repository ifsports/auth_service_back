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

    return {
        'refresh': str(refresh),
        'access': str(access_token),
    }


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

    # 2. BUSCA OS DADOS DO USUÁRIO EM PARALELO PARA GANHAR VELOCIDADE
    data_suap = {}
    data_eu = {}
    with ThreadPoolExecutor() as executor:
        # Dispara as duas requisições ao mesmo tempo
        future_meus_dados = executor.submit(
            requests.get, SUAP_API_MEUS_DADOS_URL, headers=headers_suap_api, timeout=10)
        future_eu = executor.submit(
            requests.get, SUAP_API_EU_URL, headers=headers_suap_api, timeout=10)

        # Espera os resultados e trata possíveis erros
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

    # 3. COMBINA OS DADOS E SALVA O USUÁRIO
    matricula_suap = data_suap.get('matricula')
    if not matricula_suap:
        return HttpResponseRedirect(f"{frontend_url_base}/login?error=falha_suap")

    vinculo_data = data_suap.get('vinculo', {})

    user_defaults = {
        'email': data_suap.get('email'),
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
