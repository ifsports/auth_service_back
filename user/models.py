from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, matricula, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório")
        email = self.normalize_email(email)
        # Nome é importante, então garanta que ele venha ou tenha um padrão
        nome = extra_fields.pop('nome', '')  # Pega 'nome' ou usa string vazia
        if not nome:
            # Ou defina um valor padrão se não quiser erro
            raise ValueError("O nome é obrigatório")

        user = self.model(matricula=matricula, email=email,
                          nome=nome, **extra_fields)
        # Define uma senha, mesmo que não usada para login direto
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricula, email, nome, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(matricula, email, password, nome=nome, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    matricula = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=False)
    nome = models.CharField(max_length=150)  # Campo nome é obrigatório
    # blank=True e null=True para opcionais
    campus = models.CharField(max_length=150, blank=True, null=True)
    foto = models.URLField(blank=True, null=True)
    sexo = models.CharField(max_length=10, null=True, blank=True)
    tipo_usuario = models.CharField(max_length=50, null=True, blank=True)
    curso = models.CharField(max_length=150, blank=True, null=True)
    situacao = models.CharField(max_length=150, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    # Apenas admins devem ter isso True
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'matricula'
    # 'nome' é importante para a criação do superusuário
    REQUIRED_FIELDS = ['email', 'nome']

    objects = CustomUserManager()

    def __str__(self):
        return self.nome if self.nome else self.matricula
