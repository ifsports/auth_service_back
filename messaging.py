import uuid
from datetime import datetime
from celery_app import celery_app

AUDIT_EXCHANGE = 'events_exchange'
AUDIT_TASK_NAME = 'process_audit_log'


def send_audit_log(log_payload: dict):
    try:
        routing_key = log_payload.get("event_type", "log.info")
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


def build_log_payload(request, user, event_type, operation_type, old_data=None, new_data=None, entity_id=None):
    """
    Constrói o payload de log no formato esperado pelo audit-service.
    """
    # Tenta obter o IP do request, se disponível
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
    except:
        ip = "127.0.0.1"  # Fallback

    return {
        "correlation_id": str(uuid.uuid4()),
        "campus_code": user.campus,
        "user_id": user.matricula,
        "service_origin": "auth-service",
        "event_type": event_type,
        "operation_type": operation_type,
        "entity_id": str(entity_id or user.id),
        "old_data": old_data or {},
        "new_data": new_data or {},
        "ip_address": ip
    }
