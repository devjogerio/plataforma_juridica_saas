"""
Utilitários para cache Redis otimizado
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Optional, Callable


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Gera uma chave de cache única baseada nos argumentos
    """
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"{prefix}:{key_hash}"


def cache_result(timeout: int = 300, key_prefix: str = 'default'):
    """
    Decorator para cache de resultados de funções
    
    Args:
        timeout: Tempo de expiração em segundos (padrão: 5 minutos)
        key_prefix: Prefixo para a chave do cache
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Gerar chave única
            cache_key = generate_cache_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # Tentar buscar do cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Executar função e armazenar no cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalida todas as chaves de cache que correspondem ao padrão
    
    Args:
        pattern: Padrão para buscar chaves (ex: 'clientes:*')
    
    Returns:
        Número de chaves invalidadas
    """
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        keys = redis_conn.keys(f"{settings.CACHES['default']['KEY_PREFIX']}:{pattern}")
        if keys:
            return redis_conn.delete(*keys)
        return 0
    except Exception:
        # Fallback para cache padrão
        return 0


class CacheManager:
    """
    Gerenciador de cache para operações comuns
    """
    
    @staticmethod
    def get_or_set_queryset(cache_key: str, queryset_func: Callable, timeout: int = 300) -> Any:
        """
        Busca queryset do cache ou executa e armazena
        """
        result = cache.get(cache_key)
        if result is None:
            result = list(queryset_func())
            cache.set(cache_key, result, timeout)
        return result
    
    @staticmethod
    def invalidate_model_cache(model_name: str) -> None:
        """
        Invalida cache relacionado a um modelo específico
        """
        patterns = [
            f"{model_name}:*",
            f"list:{model_name}:*",
            f"detail:{model_name}:*",
            f"stats:{model_name}:*"
        ]
        
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
    
    @staticmethod
    def cache_model_list(model_name: str, filters: dict = None, timeout: int = 300) -> str:
        """
        Gera chave de cache para listagem de modelos
        """
        filter_hash = hashlib.md5(json.dumps(filters or {}, sort_keys=True).encode()).hexdigest()
        return f"list:{model_name}:{filter_hash}"
    
    @staticmethod
    def cache_model_detail(model_name: str, pk: int) -> str:
        """
        Gera chave de cache para detalhes de modelo
        """
        return f"detail:{model_name}:{pk}"


# Decorators específicos para modelos comuns
def cache_cliente_data(timeout: int = 600):
    """Cache específico para dados de clientes (10 minutos)"""
    return cache_result(timeout=timeout, key_prefix='clientes')


def cache_processo_data(timeout: int = 300):
    """Cache específico para dados de processos (5 minutos)"""
    return cache_result(timeout=timeout, key_prefix='processos')


def cache_dashboard_data(timeout: int = 900):
    """Cache específico para dados do dashboard (15 minutos)"""
    return cache_result(timeout=timeout, key_prefix='dashboard')