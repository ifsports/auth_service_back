from rest_framework import serializers
from .models import User
from django.contrib.auth.models import Group


class UserSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = [
            'id', 'matricula', 'email', 'is_staff', 'last_login',
            'campus', 'foto', 'sexo', 'tipo_usuario', 'curso', 'situacao', 'data_nascimento', 'groups'
        ]
