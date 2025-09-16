"""
Filtros personalizados para manipulação de datas nos templates.
"""
from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def add_days(date, days):
    """
    Adiciona um número específico de dias a uma data.
    
    Args:
        date: Data base
        days: Número de dias para adicionar
        
    Returns:
        Nova data com os dias adicionados
    """
    if not date:
        return None
    
    try:
        days = int(days)
        if isinstance(date, datetime):
            return date + timedelta(days=days)
        else:
            return date + timedelta(days=days)
    except (ValueError, TypeError):
        return date