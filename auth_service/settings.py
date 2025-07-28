from datetime import timedelta
from pathlib import Path
import os
import boto3

BASE_DIR = Path(__file__).resolve().parent.parent

SSM_CLIENT = None
IS_AWS_ENVIRONMENT = 'AWS_EXECUTION_ENV' in os.environ

if IS_AWS_ENVIRONMENT:
    region = os.environ.get('AWS_REGION', 'us-east-1')
    SSM_CLIENT = boto3.client('ssm', region_name=region)


def get_secret(secret_name, default=None):
    if SSM_CLIENT:
        param_name = f"/auth-service/{secret_name}"
        try:
            response = SSM_CLIENT.get_parameter(
                Name=param_name, WithDecryption=True)
            return response['Parameter']['Value']
        except Exception as e:
            print(
                f"ERRO: Não foi possível buscar o segredo '{param_name}' do AWS Parameter Store. {e}")
            return default
    else:
        # Fallback para desenvolvimento local
        return os.environ.get(secret_name, default)


SECRET_KEY = get_secret('SECRET_KEY')
DB_PASSWORD = get_secret('DB_PASSWORD')
SUAP_CLIENT_SECRET = get_secret('SUAP_CLIENT_SECRET')
JWT_SIGNING_KEY = get_secret('JWT_SIGNING_KEY')  # <-- ADICIONE ESTA LINHA

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CORS_ALLOWED_ORIGINS = os.environ.get(
    'DJANGO_CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    'user', 'rest_framework', 'rest_framework_simplejwt', 'corsheaders',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "auth_service.urls"
WSGI_APPLICATION = "auth_service.wsgi.application"

TEMPLATES = [
    {"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
     "OPTIONS": {
         "context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",],
    },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': DB_PASSWORD,  # Usando a variável segura que buscamos acima
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

AUTH_USER_MODEL = 'user.User'

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- SUAP ---
SUAP_CLIENT_ID = os.environ.get("SUAP_CLIENT_ID")

# --- JWT ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',)
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "VERIFYING_KEY": None, "AUDIENCE": None, "ISSUER": None, "JWK_URL": None, "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",), "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id", "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type", "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
}

# --- Frontend URLs ---
FRONTEND_APP_URL = os.environ.get("FRONTEND_APP_URL", "http://localhost:3000")
FRONTEND_LOGIN_SUCCESS_PATH = os.environ.get(
    "FRONTEND_LOGIN_SUCCESS_PATH", "/auth/handle-token")
FRONTEND_LOGIN_ERROR_PATH = os.environ.get("FRONTEND_LOGIN_ERROR_PATH", "/")
