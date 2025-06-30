from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
app_name = 'user'

urlpatterns = [
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/suap/callback/", views.suap_oauth_callback_view, name="suap_oauth_callback"),

    # --- ROTAS DA API (USAM JWT GERADO PELO CALLBACK ACIMA) ---
    path("api/v1/auth/logout/", views.LogoutView.as_view(), name="api_logout"),
    path("api/v1/auth/users/me/", views.UserMeView.as_view(), name="api_user_me"),
    path("api/v1/auth/users/<int:id>/", views.UserDetailView.as_view(), name="api_user_detail"),
    path("api/v1/auth/users/", views.ValidateUsersByMatriculaView.as_view(), name="api_user_list"),
]
