from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from user.models import User
import os


class Command(BaseCommand):
    help = 'Cria um usuário Organizador para um campus específico.'

    def add_arguments(self, parser):
        parser.add_argument('--campus', type=str,
                            help='Código do campus (ex: PF, CN)', required=True)
        parser.add_argument('--email', type=str,
                            help='Email para o novo organizador', required=True)
        parser.add_argument('--password', type=str,
                            help='Senha para o novo organizador', required=True)

    def handle(self, *args, **options):
        campus_code = options['campus'].upper()
        email = options['email']
        password = options['password']

        matricula = f'organizador_{campus_code}'.lower()
        nome = f'Organizador {campus_code}'

        if User.objects.filter(matricula=matricula).exists():
            self.stdout.write(self.style.NOTICE(
                f'Organizador para o campus {campus_code} já existe.'))
            return

        # Garante que o grupo "Organizador" existe
        organizador_group, created = Group.objects.get_or_create(
            name='Organizador')
        if created:
            self.stdout.write(self.style.SUCCESS(
                'Grupo "Organizador" criado.'))

        # Garante que o grupo "Jogador" existe
        Group.objects.get_or_create(name='Jogador')

        try:

            user = User.objects.create_user(
                matricula=matricula,
                email=email,
                nome=nome,
                password=password,
                campus=campus_code,
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()

            user.groups.add(organizador_group)

            self.stdout.write(self.style.SUCCESS(
                f'Usuário organizador "{nome}" (com permissão de superusuário) criado com sucesso!'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Erro ao criar organizador: {e}'))
