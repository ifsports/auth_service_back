from django.contrib.auth.models import User
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
        "scope": "identificacao email documentos_pessoais",
    }

    response = requests.post(
        "https://suap.ifrn.edu.br/o/token/", data=request_data)

    print(response.json())

    token = response.json().get("access_token")

    response2 = requests.get(
        "https://suap.ifrn.edu.br/api/eu", headers={
            "Authorization": f"Bearer {token}"  
        })
    print(response2.json())

    if User.objects.filter(username=response2.json().get("identificacao")).exists():
        user = User.objects.get(username=response2.json().get("identificacao"))
        token = Token.objects.get(user=user)

    else:

        user = User.objects.create_user(
        username=response2.json().get("identificacao"),
        first_name=response2.json().get("primeiro_nome"),
        last_name=response2.json().get("ultimo_nome"),
        email=response2.json().get("email_google_classroom"),
    )
        token = Token.objects.create(user=user)


    key = token.key

    # Parameters or Cookies

    return HttpResponseRedirect(f"http://localhost:3000?token={key}")