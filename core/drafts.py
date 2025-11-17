from typing import Any, Dict, Optional
import json
import hmac
import hashlib
import time

from django.core.cache import cache
from django.conf import settings


def _draft_key(user_id: int, form_slug: str, object_id: Optional[str]) -> str:
    """Gera a chave única do rascunho para usuário/formulário/objeto"""
    obj = object_id or "new"
    return f"drafts:{user_id}:{form_slug}:{obj}"


def _compute_hash(payload: Dict[str, Any]) -> str:
    """Calcula HMAC SHA256 do payload usando SECRET_KEY"""
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hmac.new(settings.SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()


def save_draft(user, form_slug: str, object_id: Optional[str], payload: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
    """Salva rascunho no cache com TTL e HMAC de integridade"""
    max_kb = getattr(settings, 'CHECKPOINT_MAX_PAYLOAD_KB', 128)
    if len(json.dumps(payload, default=str).encode()) > max_kb * 1024:
        raise ValueError('Payload excede o tamanho máximo permitido')

    data = {
        'payload': payload,
        'timestamp': int(time.time()),
        'version': payload.get('version', 1),
        'schemaVersion': payload.get('schemaVersion', 1),
    }
    data['hash'] = _compute_hash(data['payload'])

    key = _draft_key(user.id, form_slug, object_id)
    ttl_final = ttl if ttl is not None else getattr(settings, 'CHECKPOINT_TTL_SECONDS', 1200)
    cache.set(key, data, ttl_final)
    return data


def load_draft(user, form_slug: str, object_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Carrega rascunho do cache e valida integridade"""
    key = _draft_key(user.id, form_slug, object_id)
    data = cache.get(key)
    if not data:
        return None
    expected = _compute_hash(data.get('payload', {}))
    if expected != data.get('hash'):
        return None
    return data


def delete_draft(user, form_slug: str, object_id: Optional[str]) -> bool:
    """Remove rascunho do cache"""
    key = _draft_key(user.id, form_slug, object_id)
    return bool(cache.delete(key))