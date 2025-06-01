from django.urls import path
from . import views 

app_name = 'user'

urlpatterns = [
    # --- ROTA PRINCIPAL DE LOGIN SUAP (FLUXO DE REDIRECIONAMENTO) ---
    # Esta é a URL que você foi configurada como Redirect URI no SUAP
    # e usar no link de login do seu frontend.
    path("auth/suap/callback/", views.suap_oauth_callback_view, name="suap_oauth_callback"),

    # --- ROTAS DA API (USAM JWT GERADO PELO CALLBACK ACIMA) ---
    path("api/v1/auth/logout/", views.LogoutView.as_view(), name="api_logout"),
    path("api/v1/auth/users/me/", views.UserMeView.as_view(), name="api_user_me"),
    path("api/v1/auth/users/<int:id>/", views.UserDetailView.as_view(), name="api_user_detail"),
    path("api/v1/auth/users/", views.ValidateUsersByMatriculaView.as_view(), name="api_user_list"),
]
