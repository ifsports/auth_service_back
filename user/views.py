from .models import User
from rest_framework.authtoken.models import Token
from django.shortcuts import render, redirect
import requests
from django.http import HttpResponseRedirect, JsonResponse


def suap_login(request):
    code = request.GET.get("code")
    print(code)

    request_data = {
        "client_id": "AcFNXdcMNZhtDKI3LMYhrtzC5xTeisjKmq41opDR",
        "client_secret": "MpWiND3lzWJ1wXOPJebGPcMgWzsRsmP7PxlVjmYWS0Ro1BGanIoj5s0XaIBKWYYAWH4PD1syi80rAdx6JxjxywkPNz8IEO8p50k0oDZurauYWe3EwHJyptCV9Mlze57I",
        "code": code,
        "grant_type": "authorization_code",
        "scope": "identificacao email dados_pessoais",
    }

    response = requests.post(
        "https://suap.ifrn.edu.br/o/token/", data=request_data)

    print(response.json())

    token = response.json().get("access_token")

    response2 = requests.get(
        "https://suap.ifrn.edu.br/api/eu", headers={
            "Authorization": f"Bearer {token}"
        })
    response2 = response2.json()
    # print(f'API/EU{response2}')

    response3 = requests.get(
        "https://suap.ifrn.edu.br/api/rh/meus-dados", headers={
            "Authorization": f"Bearer {token}"
        })
    response3 = response3.json()
    # print(f'API/MEUS-DADOS{response3}')

    vinculo = response3.get('vinculo')

    # if User.objects.filter(matricula=response2.get("identificacao")).exists():
    #     user = User.objects.get(
    #         matricula=response2.get("identificacao"))
    #     token = Token.objects.get(user=user)

    # else:

    user_data = {
        'matricula': response3.get('matricula'),
        'email': response2.get('email'),
        'nome': vinculo.get('nome'),
        'campus': vinculo.get('campus'),
        'foto': response3.get('url_foto_150x200'),
        'sexo': response2.get('sexo', ''),
        'tipo_usuario': response3.get('tipo_vinculo', ''),
        'curso': vinculo.get('curso'),
        'situacao': vinculo.get('situacao', ''),
        'data_nascimento': response3.get('data_nascimento'),
    }

    user, created = User.objects.update_or_create(
        matricula=user_data['matricula'],
        defaults=user_data
    )

    token, _ = Token.objects.get_or_create(user=user)

    key = token.key

    return HttpResponseRedirect(f"http://localhost:3000?token={key}")
