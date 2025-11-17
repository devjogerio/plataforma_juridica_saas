import django_filters
from django.db import models
from clientes.models import Cliente
from processos.models import Processo
from financeiro.models import Transacao


class ClienteFilter(django_filters.FilterSet):
    """Filtros avançados para o modelo Cliente"""
    
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email')
    cpf_cnpj = django_filters.CharFilter(lookup_expr='icontains', label='CPF/CNPJ')
    
    data_cadastro_inicio = django_filters.DateFilter(
        field_name='created_at', lookup_expr='gte', label='Data cadastro (início)'
    )
    data_cadastro_fim = django_filters.DateFilter(
        field_name='created_at', lookup_expr='lte', label='Data cadastro (fim)'
    )
    
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'cpf_cnpj']


class ProcessoFilter(django_filters.FilterSet):
    """Filtros avançados para o modelo Processo"""
    
    numero = django_filters.CharFilter(lookup_expr='icontains', label='Número do processo')
    titulo = django_filters.CharFilter(lookup_expr='icontains', label='Título')
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.all(),
        label='Cliente'
    )
    
    status = django_filters.ChoiceFilter(
        choices=[('ativo', 'Ativo'), ('arquivado', 'Arquivado'), ('encerrado', 'Encerrado')],
        label='Status'
    )
    
    data_abertura_inicio = django_filters.DateFilter(
        field_name='data_abertura', lookup_expr='gte', label='Data abertura (início)'
    )
    data_abertura_fim = django_filters.DateFilter(
        field_name='data_abertura', lookup_expr='lte', label='Data abertura (fim)'
    )
    
    urgente = django_filters.BooleanFilter(label='Urgente')
    
    class Meta:
        model = Processo
        fields = ['numero', 'titulo', 'descricao', 'cliente', 'status', 'urgente']


class TransacaoFilter(django_filters.FilterSet):
    """Filtros avançados para o modelo Transacao (Financeiro)"""
    
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    valor_min = django_filters.NumberFilter(field_name='valor', lookup_expr='gte', label='Valor mínimo')
    valor_max = django_filters.NumberFilter(field_name='valor', lookup_expr='lte', label='Valor máximo')
    
    tipo = django_filters.ChoiceFilter(
        choices=[('receita', 'Receita'), ('despesa', 'Despesa')],
        label='Tipo'
    )
    
    status = django_filters.ChoiceFilter(
        choices=[('pendente', 'Pendente'), ('pago', 'Pago'), ('vencido', 'Vencido')],
        label='Status'
    )
    
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.all(),
        label='Cliente'
    )
    
    processo = django_filters.ModelChoiceFilter(
        queryset=Processo.objects.all(),
        label='Processo'
    )
    
    class Meta:
        model = Transacao
        fields = ['descricao', 'tipo', 'status', 'cliente', 'processo']


def get_filter_class_for_entity(entity_type):
    """
    Retorna a classe de filtro apropriada com base no tipo de entidade.
    
    Args:
        entity_type: Tipo de entidade ('clientes', 'processos', 'financeiro', etc.)
    
    Returns:
        Classe FilterSet apropriada ou None se não encontrada
    """
    filter_mapping = {
        'clientes': ClienteFilter,
        'processos': ProcessoFilter,
        'financeiro': TransacaoFilter,
        'transacoes': TransacaoFilter,
    }
    return filter_mapping.get(entity_type.lower())


def apply_saved_filter(queryset, filtro_salvo, user=None):
    """
    Aplica um filtro salvo a um queryset.
    
    Args:
        queryset: QuerySet Django a ser filtrado
        filtro_salvo: Instância de FiltroSalvo
        user: Usuário opcional para verificar permissões
    
    Returns:
        QuerySet filtrado
    """
    if not filtro_salvo or not filtro_salvo.configuracao:
        return queryset
    
    # Verifica permissões se usuário fornecido
    if user and not filtro_salvo.is_public and filtro_salvo.criado_por != user:
        raise PermissionError("Usuário não tem permissão para usar este filtro")
    
    try:
        import json
        filtros = json.loads(filtro_salvo.configuracao)
        
        # Aplica cada filtro do JSON
        for field, value in filtros.items():
            if value is not None and value != '':
                # Suporta lookups como __icontains, __gte, etc.
                if '__' in field:
                    queryset = queryset.filter(**{field: value})
                else:
                    # Filtro simples de igualdade
                    queryset = queryset.filter(**{field: value})
        
        return queryset
        
    except (json.JSONDecodeError, TypeError) as e:
        # Log do erro e retorna queryset não filtrado
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao aplicar filtro salvo {filtro_salvo.id}: {e}")
        return queryset