from django.contrib import admin
from django.urls import path
from .views import *


urlpatterns = [
    path("login_suap/", suap_login, name="suap_login"),
]
