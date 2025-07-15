import json
from datetime import datetime
from celery_app import celery_app  # <--- Importa nosso novo objeto Celery

AUDIT_EXCHANGE = 'events_exchange'  # O nome da exchange definida no audit-service
AUDIT_TASK_NAME = 'process_audit_log'  # O nome da tarefa no audit-service


def send_audit_log(log_payload: dict):
    """
    Envia uma tarefa de auditoria para o RabbitMQ usando Celery.
    """
    try:
        # O "assunto" da mensagem é o routing_key
        routing_key = log_payload.get("event_type", "log.info")

        # Usa o método send_task do Celery
        celery_app.send_task(
            name=AUDIT_TASK_NAME,
            args=[log_payload],
            exchange=AUDIT_EXCHANGE,
            routing_key=routing_key
        )
        print(
            f" [AUDIT] Tarefa '{AUDIT_TASK_NAME}' enviada para a exchange '{AUDIT_EXCHANGE}' com routing_key '{routing_key}'.")

    except Exception as e:
        print(f"ERRO DE AUDITORIA: Falha ao enviar tarefa Celery. Erro: {e}")

# A função build_log_payload continua exatamente a mesma.


def build_log_payload(user, event_type, operation_type, old_data=None, new_data=None):
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user.matricula,
        "campus_id": user.campus,
        "event_type": event_type,
        "service_origin": "auth-service",
        "entity_type": "user",
        "entity_id": user.id,
        "operation_type": operation_type,
        "old_data": old_data or {},
        "new_data": new_data or {}
    }
