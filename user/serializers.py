from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer que representa o modelo completo de um usuário.
    Usado para retornar dados detalhados de usuários.
    """
    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'matricula', 'email', 'nome', 'campus', 'foto', 'sexo',
            'tipo_usuario', 'curso', 'situacao', 'data_nascimento',
            'is_active', 'is_staff', 'groups',
        ]
        read_only_fields = fields


# --- ADIÇÕES PARA DOCUMENTAÇÃO ---

class LoginRequestSerializer(serializers.Serializer):
    """
    Descreve o corpo da requisição para o endpoint de login.
    """
    matricula = serializers.CharField(
        required=True, help_text="Matrícula do organizador/usuário.")
    password = serializers.CharField(
        required=True, help_text="Senha do organizador.", style={'input_type': 'password'})


class TokenResponseSerializer(serializers.Serializer):
    """
    Descreve a resposta bem-sucedida do endpoint de login, contendo os tokens.
    """
    refresh = serializers.CharField(
        read_only=True, help_text="Token para renovar a sessão.")
    access = serializers.CharField(
        read_only=True, help_text="Token de acesso a ser usado nas requisições.")


class MatriculasRequestSerializer(serializers.Serializer):
    """
    Descreve o corpo da requisição para endpoints que recebem uma lista de matrículas.
    """
    user_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="Uma lista de strings contendo as matrículas a serem validadas."
    )
