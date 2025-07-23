import json
import uuid
from datetime import datetime, timezone
from celery_app import celery_app

# Exceção principal de conexão do Celery
from kombu.exceptions import OperationalError

AUDIT_EXCHANGE = 'events_exchange'
AUDIT_TASK_NAME = 'process_audit_log'


def send_audit_log(log_payload: dict):
    try:
        routing_key = log_payload.get("event_type", "log.info")

        celery_app.send_task(
            name=AUDIT_TASK_NAME,
            args=[log_payload],
            exchange=AUDIT_EXCHANGE,
            routing_key=routing_key,
            retry=True,
            retry_policy={
                'max_retries': 3,          # Tenta no máximo 3 vezes
                'interval_start': 0.5,     # Começa esperando 0.5s
                'interval_step': 0.5,      # Aumenta o tempo de espera em 0.5s a cada tentativa
                'interval_max': 2.0,       # O tempo de espera não passará de 2s
            }
        )

        print(
            f" [AUDIT] Tarefa '{AUDIT_TASK_NAME}' enviada para a exchange '{AUDIT_EXCHANGE}' com routing_key '{routing_key}'.")

    except OperationalError as exc:
        print(
            f"ERRO DE AUDITORIA: Falha de conexão ao tentar enviar tarefa. A tarefa será tentada novamente. Erro: {exc}")
    except Exception as e:
        print(f"ERRO DE AUDITORIA: Falha genérica ao enviar tarefa. Erro: {e}")


def build_log_payload(request, user, event_type, operation_type, old_data=None, new_data=None, entity_id=None):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
    except:
        ip = "127.0.0.1"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": str(uuid.uuid4()),
        "campus_code": user.campus,
        "user_id": user.matricula,
        "service_origin": "auth_service_back",
        "event_type": event_type,
        "operation_type": operation_type,
        "entity_type": "user",
        "entity_id": str(entity_id or user.id),
        "old_data": old_data or {},
        "new_data": new_data or {},
        "ip_address": ip
    }
