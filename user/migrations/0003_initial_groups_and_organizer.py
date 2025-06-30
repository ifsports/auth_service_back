from django.db import migrations
import os


def create_initial_data(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('user', 'User')

    jogador_group, created = Group.objects.get_or_create(name='Jogador')
    if created:
        print('Grupo "Jogador" criado.')

    organizador_group, created = Group.objects.get_or_create(
        name='Organizador')
    if created:
        print('Grupo "Organizador" criado.')

    ADMIN_EMAIL = 'ifsports@admin.com'
    ADMIN_PASS = os.environ.get('DEFAULT_ADMIN_PASS', 'Pass@2025')
    ADMIN_MATRICULA = 'ifsports_admin'

    if not User.objects.filter(matricula=ADMIN_MATRICULA).exists():
        print(f"Criando superusuário organizador: {ADMIN_EMAIL}")

        admin_user = User.objects.create_superuser(
            email=ADMIN_EMAIL,
            matricula=ADMIN_MATRICULA,
            nome='Organizador Padrão',
            password=ADMIN_PASS
        )

        admin_user.groups.add(organizador_group)
        print("Superusuário adicionado ao grupo 'Organizador'.")
    else:
        print(f"Superusuário com matrícula {ADMIN_MATRICULA} já existe.")


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
