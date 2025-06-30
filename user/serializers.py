# your_app_name/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth.models import Group


class UserSerializer(serializers.ModelSerializer):
    # StringRelatedField vai retornar uma lista com os nomes dos grupos. Ex: ["Jogador"]
    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',  # Adicionado para referenciar o usuário pela PK
            'matricula',
            'email',
            'nome',
            'campus',
            'foto',
            'sexo',
            'tipo_usuario',
            'curso',
            'situacao',
            'data_nascimento',
            'is_active',
            'is_staff',
            'groups',
            # Adicionar 'last_login' ou outros campos se necessário
        ]
        # Campos que são definidos pelo SUAP ou internamente e não devem ser alterados diretamente pela API.
        read_only_fields = [
            'id', 'matricula', 'email', 'is_staff', 'last_login',
            'campus', 'foto', 'sexo', 'tipo_usuario', 'curso', 'situacao', 'data_nascimento', 'groups'
            # Basicamente, após a sincronização com o SUAP, a maioria dos dados do usuário é apenas para leitura.
        ]
