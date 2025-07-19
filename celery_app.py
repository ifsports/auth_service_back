from celery import Celery
from kombu import Exchange, Queue
import os

rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')

celery_app = Celery('auth_tasks', broker=rabbitmq_url)

# Define a exchange e a fila exatamente como no audit-service.
events_exchange = Exchange('events_exchange', type='topic')
audit_queue = Queue(
    'audit_queue',
    events_exchange,
    routing_key='#'
)

celery_app.conf.task_queues = (audit_queue,)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

# Força a declaração da exchange e da fila na inicialização do django.
try:
    with celery_app.connection_for_write() as conn:
        # A declaração da fila também declara a exchange à qual ela está ligada.
        audit_queue.declare(channel=conn.channel())
        print(
            ">>> [Celery Producer] Exchange 'events_exchange' e Fila 'audit_queue' declaradas com sucesso. <<<")
except Exception as e:
    print(
        f">>> [Celery Producer] AVISO: Não foi possível declarar a fila na inicialização. Celery tentará novamente. Erro: {e} <<<")
