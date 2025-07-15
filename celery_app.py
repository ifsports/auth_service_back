from celery import Celery
import os

# Pega a URL do RabbitMQ a partir das variáveis de ambiente
rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://user:password@rabbitmq:5672/')

# Cria uma instância Celery simples apenas para ENVIAR tarefas.
# O nome 'auth_tasks' é apenas um identificador local.
celery_app = Celery('auth_tasks', broker=rabbitmq_url)

# Configurações para garantir que a comunicação funcione
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)
