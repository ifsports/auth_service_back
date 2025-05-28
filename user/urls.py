from django.contrib import admin
from django.urls import path
from .views import *


urlpatterns = [
    path("api/v1/auth/login", suap_login, name="suap_login"),
]
