import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Processo, Andamento, Prazo
from clientes.models import Cliente
from django.contrib.auth import get_user_model

User = get_user_model()


class ProcessoFilter(django_filters.FilterSet):
    """Filtros para processos"""
    
    # Filtros básicos
    numero_processo = django_filters.CharFilter(
        field_name='numero_processo',
        lookup_expr='icontains',
        label='Número do Processo'
    )
    
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.all(),
        label='Cliente'
    )
    
    cliente_nome = django_filters.CharFilter(
        field_name='cliente__nome_razao_social',
        lookup_expr='icontains',
        label='Nome do Cliente'
    )
    
    tipo_processo = django_filters.CharFilter(
        field_name='tipo_processo',
        lookup_expr='icontains',
        label='Tipo de Processo'
    )
    
    area_direito = django_filters.ChoiceFilter(
        choices=Processo.AREA_DIREITO_CHOICES,
        label='Área do Direito'
    )
    
    status = django_filters.ChoiceFilter(
        choices=Processo.STATUS_CHOICES,
        label='Status'
    )
    
    responsavel = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(is_active=True),
        label='Responsável'
    )
    
    # Filtros por data
    data_inicio = django_filters.DateFilter(
        field_name='data_inicio',
        label='Data de Início'
    )
    
    data_inicio_after = django_filters.DateFilter(
        field_name='data_inicio',
        lookup_expr='gte',
        label='Data de Início (a partir de)'
    )
    
    data_inicio_before = django_filters.DateFilter(
        field_name='data_inicio',
        lookup_expr='lte',
        label='Data de Início (até)'
    )
    
    data_encerramento = django_filters.DateFilter(
        field_name='data_encerramento',
        label='Data de Encerramento'
    )
    
    # Filtros por valor
    valor_causa_min = django_filters.NumberFilter(
        field_name='valor_causa',
        lookup_expr='gte',
        label='Valor da Causa (mínimo)'
    )
    
    valor_causa_max = django_filters.NumberFilter(
        field_name='valor_causa',
        lookup_expr='lte',
        label='Valor da Causa (máximo)'
    )
    
    # Filtros por localização
    comarca = django_filters.CharFilter(
        field_name='comarca',
        lookup_expr='icontains',
        label='Comarca'
    )
    
    vara = django_filters.CharFilter(
        field_name='vara',
        lookup_expr='icontains',
        label='Vara'
    )
    
    # Filtros especiais
    sem_andamentos = django_filters.BooleanFilter(
        method='filter_sem_andamentos',
        label='Sem Andamentos'
    )
    
    com_prazos_vencidos = django_filters.BooleanFilter(
        method='filter_com_prazos_vencidos',
        label='Com Prazos Vencidos'
    )
    
    criados_ultima_semana = django_filters.BooleanFilter(
        method='filter_criados_ultima_semana',
        label='Criados na Última Semana'
    )
    
    class Meta:
        model = Processo
        fields = [
            'numero_processo', 'cliente', 'cliente_nome', 'tipo_processo',
            'area_direito', 'status', 'responsavel', 'data_inicio',
            'data_inicio_after', 'data_inicio_before', 'data_encerramento',
            'valor_causa_min', 'valor_causa_max', 'comarca', 'vara'
        ]
    
    def filter_sem_andamentos(self, queryset, name, value):
        """Filtrar processos sem andamentos"""
        if value:
            return queryset.filter(andamentos__isnull=True)
        return queryset
    
    def filter_com_prazos_vencidos(self, queryset, name, value):
        """Filtrar processos com prazos vencidos"""
        if value:
            hoje = timezone.now().date()
            return queryset.filter(
                prazos__status='pendente',
                prazos__data_limite__lt=hoje
            ).distinct()
        return queryset
    
    def filter_criados_ultima_semana(self, queryset, name, value):
        """Filtrar processos criados na última semana"""
        if value:
            uma_semana_atras = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=uma_semana_atras)
        return queryset


class AndamentoFilter(django_filters.FilterSet):
    """Filtros para andamentos"""
    
    processo = django_filters.ModelChoiceFilter(
        queryset=Processo.objects.all(),
        label='Processo'
    )
    
    processo_numero = django_filters.CharFilter(
        field_name='processo__numero_processo',
        lookup_expr='icontains',
        label='Número do Processo'
    )
    
    tipo_andamento = django_filters.CharFilter(
        field_name='tipo_andamento',
        lookup_expr='icontains',
        label='Tipo de Andamento'
    )
    
    usuario = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(is_active=True),
        label='Usuário'
    )
    
    # Filtros por data
    data_andamento = django_filters.DateFilter(
        field_name='data_andamento',
        label='Data do Andamento'
    )
    
    data_andamento_after = django_filters.DateFilter(
        field_name='data_andamento',
        lookup_expr='gte',
        label='Data do Andamento (a partir de)'
    )
    
    data_andamento_before = django_filters.DateFilter(
        field_name='data_andamento',
        lookup_expr='lte',
        label='Data do Andamento (até)'
    )
    
    # Filtros especiais
    ultima_semana = django_filters.BooleanFilter(
        method='filter_ultima_semana',
        label='Última Semana'
    )
    
    ultimo_mes = django_filters.BooleanFilter(
        method='filter_ultimo_mes',
        label='Último Mês'
    )
    
    class Meta:
        model = Andamento
        fields = [
            'processo', 'processo_numero', 'tipo_andamento', 'usuario',
            'data_andamento', 'data_andamento_after', 'data_andamento_before'
        ]
    
    def filter_ultima_semana(self, queryset, name, value):
        """Filtrar andamentos da última semana"""
        if value:
            uma_semana_atras = timezone.now().date() - timedelta(days=7)
            return queryset.filter(data_andamento__gte=uma_semana_atras)
        return queryset
    
    def filter_ultimo_mes(self, queryset, name, value):
        """Filtrar andamentos do último mês"""
        if value:
            um_mes_atras = timezone.now().date() - timedelta(days=30)
            return queryset.filter(data_andamento__gte=um_mes_atras)
        return queryset


class PrazoFilter(django_filters.FilterSet):
    """Filtros para prazos"""
    
    processo = django_filters.ModelChoiceFilter(
        queryset=Processo.objects.all(),
        label='Processo'
    )
    
    processo_numero = django_filters.CharFilter(
        field_name='processo__numero_processo',
        lookup_expr='icontains',
        label='Número do Processo'
    )
    
    tipo_prazo = django_filters.CharFilter(
        field_name='tipo_prazo',
        lookup_expr='icontains',
        label='Tipo de Prazo'
    )
    
    cumprido = django_filters.BooleanFilter(
        field_name='cumprido',
        label='Cumprido'
    )
    
    prioridade = django_filters.ChoiceFilter(
        choices=Prazo.PRIORIDADE_CHOICES,
        label='Prioridade'
    )
    
    responsavel = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(is_active=True),
        label='Responsável'
    )
    
    # Filtros por data
    data_limite = django_filters.DateFilter(
        field_name='data_limite',
        label='Data Limite'
    )
    
    data_limite_after = django_filters.DateFilter(
        field_name='data_limite',
        lookup_expr='gte',
        label='Data Limite (a partir de)'
    )
    
    data_limite_before = django_filters.DateFilter(
        field_name='data_limite',
        lookup_expr='lte',
        label='Data Limite (até)'
    )
    
    # Filtros especiais
    vencidos = django_filters.BooleanFilter(
        method='filter_vencidos',
        label='Vencidos'
    )
    
    criticos = django_filters.BooleanFilter(
        method='filter_criticos',
        label='Críticos (próximos 3 dias)'
    )
    
    proximos = django_filters.BooleanFilter(
        method='filter_proximos',
        label='Próximos (próximos 7 dias)'
    )
    
    pendentes = django_filters.BooleanFilter(
        method='filter_pendentes',
        label='Pendentes'
    )
    
    class Meta:
        model = Prazo
        fields = [
            'processo', 'processo_numero', 'tipo_prazo', 'cumprido', 'prioridade',
            'responsavel', 'data_limite', 'data_limite_after',
            'data_limite_before'
        ]
    
    def filter_vencidos(self, queryset, name, value):
        """Filtrar prazos vencidos"""
        if value:
            hoje = timezone.now().date()
            return queryset.filter(
                cumprido=False,
                data_limite__lt=hoje
            )
        return queryset
    
    def filter_criticos(self, queryset, name, value):
        """Filtrar prazos críticos (próximos 3 dias)"""
        if value:
            hoje = timezone.now().date()
            tres_dias = hoje + timedelta(days=3)
            return queryset.filter(
                cumprido=False,
                data_limite__lte=tres_dias,
                data_limite__gte=hoje
            )
        return queryset
    
    def filter_proximos(self, queryset, name, value):
        """Filtrar prazos próximos (próximos 7 dias)"""
        if value:
            hoje = timezone.now().date()
            sete_dias = hoje + timedelta(days=7)
            return queryset.filter(
                cumprido=False,
                data_limite__lte=sete_dias,
                data_limite__gte=hoje
            )
        return queryset
    
    def filter_pendentes(self, queryset, name, value):
        """Filtrar apenas prazos pendentes"""
        if value:
            return queryset.filter(cumprido=False)
        return queryset