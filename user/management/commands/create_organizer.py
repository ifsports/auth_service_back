from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from user.models import User
import os


class Command(BaseCommand):
    help = 'Cria os usuários Organizadores iniciais com base na variável de ambiente INITIAL_CAMPUS_CODES.'

    def handle(self, *args, **options):
        initial_campus_codes = os.environ.get('INITIAL_CAMPUS_CODES')
        default_password = os.environ.get('DEFAULT_ORGANIZER_PASS')

        if not initial_campus_codes or not default_password:
            self.stdout.write(self.style.WARNING(
                'Variáveis INITIAL_CAMPUS_CODES ou DEFAULT_ORGANIZER_PASS não definidas. Nenhum organizador será criado.'))
            return

        self.stdout.write("Verificando e criando organizadores iniciais...")

        # Garante que os grupos existem antes do loop
        organizador_group, _ = Group.objects.get_or_create(name='Organizador')
        Group.objects.get_or_create(name='Jogador')

        campus_list = [code.strip()
                       for code in initial_campus_codes.split(',') if code.strip()]

        for campus_code in campus_list:
            campus_code_upper = campus_code.upper()
            matricula = f'organizador_{campus_code_upper}'.lower()
            nome = f'Organizador {campus_code_upper}'
            email = f'organizador.{matricula}@ifrn.edu.br'

            if User.objects.filter(matricula=matricula).exists():
                self.stdout.write(self.style.NOTICE(
                    f'Organizador para o campus {campus_code_upper} já existe.'))
                continue  # Pula para o próximo

            try:
                user = User.objects.create_user(
                    matricula=matricula,
                    email=email,
                    nome=nome,
                    password=default_password,
                    campus=campus_code_upper,
                )
                user.is_staff = True
                user.is_superuser = True
                user.save()
                user.groups.add(organizador_group)
                self.stdout.write(self.style.SUCCESS(
                    f'--> Usuário "{nome}" criado com sucesso!'
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f'--> Erro ao criar organizador para {campus_code_upper}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            'Criação de organizadores concluída.'))
