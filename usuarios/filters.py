import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Usuario


class UsuarioFilter(django_filters.FilterSet):
    """Filtros para usuários"""
    
    # Filtros básicos
    username = django_filters.CharFilter(
        field_name='username',
        lookup_expr='icontains',
        label='Nome de Usuário'
    )
    
    first_name = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='icontains',
        label='Primeiro Nome'
    )
    
    last_name = django_filters.CharFilter(
        field_name='last_name',
        lookup_expr='icontains',
        label='Último Nome'
    )
    
    nome_completo = django_filters.CharFilter(
        method='filter_nome_completo',
        label='Nome Completo'
    )
    
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='E-mail'
    )
    
    # Filtros por OAB
    oab_numero = django_filters.CharFilter(
        field_name='oab_numero',
        lookup_expr='icontains',
        label='Número da OAB'
    )
    
    oab_uf = django_filters.ChoiceFilter(
        choices=[
            ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
            ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
            ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
            ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
            ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
            ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
            ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'),
            ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
            ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
            ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
        ],
        label='UF da OAB'
    )
    
    # Filtros por contato
    telefone = django_filters.CharFilter(
        field_name='telefone',
        lookup_expr='icontains',
        label='Telefone'
    )
    
    # Filtros por cargo e departamento
    cargo = django_filters.CharFilter(
        field_name='cargo',
        lookup_expr='icontains',
        label='Cargo'
    )
    
    departamento = django_filters.CharFilter(
        field_name='departamento',
        lookup_expr='icontains',
        label='Departamento'
    )
    
    # Filtros por status
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Ativo'
    )
    
    is_staff = django_filters.BooleanFilter(
        field_name='is_staff',
        label='Staff'
    )
    
    is_superuser = django_filters.BooleanFilter(
        field_name='is_superuser',
        label='Superusuário'
    )
    
    # Filtros por data
    date_joined = django_filters.DateFilter(
        field_name='date_joined',
        label='Data de Cadastro'
    )
    
    date_joined_after = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='gte',
        label='Cadastrado a partir de'
    )
    
    date_joined_before = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='lte',
        label='Cadastrado até'
    )
    
    last_login = django_filters.DateFilter(
        field_name='last_login',
        label='Último Login'
    )
    
    last_login_after = django_filters.DateFilter(
        field_name='last_login',
        lookup_expr='gte',
        label='Último Login a partir de'
    )
    
    last_login_before = django_filters.DateFilter(
        field_name='last_login',
        lookup_expr='lte',
        label='Último Login até'
    )
    
    # Filtros especiais
    com_oab = django_filters.BooleanFilter(
        method='filter_com_oab',
        label='Com OAB'
    )
    
    sem_oab = django_filters.BooleanFilter(
        method='filter_sem_oab',
        label='Sem OAB'
    )
    
    online = django_filters.BooleanFilter(
        method='filter_online',
        label='Online (últimos 15 minutos)'
    )
    
    cadastrados_ultima_semana = django_filters.BooleanFilter(
        method='filter_cadastrados_ultima_semana',
        label='Cadastrados na Última Semana'
    )
    
    cadastrados_ultimo_mes = django_filters.BooleanFilter(
        method='filter_cadastrados_ultimo_mes',
        label='Cadastrados no Último Mês'
    )
    
    nunca_logaram = django_filters.BooleanFilter(
        method='filter_nunca_logaram',
        label='Nunca Fizeram Login'
    )
    
    com_processos = django_filters.BooleanFilter(
        method='filter_com_processos',
        label='Com Processos'
    )
    
    sem_processos = django_filters.BooleanFilter(
        method='filter_sem_processos',
        label='Sem Processos'
    )
    
    # Filtros por grupos/permissões
    grupo = django_filters.CharFilter(
        field_name='groups__name',
        lookup_expr='icontains',
        label='Grupo'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'oab_numero',
            'oab_uf', 'telefone', 'cargo', 'departamento', 'is_active',
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
    
    def filter_nome_completo(self, queryset, name, value):
        """Filtrar por nome completo (first_name + last_name)"""
        if value:
            return queryset.filter(
                Q(first_name__icontains=value) |
                Q(last_name__icontains=value) |
                Q(first_name__icontains=value.split()[0]) &
                Q(last_name__icontains=' '.join(value.split()[1:]))
            )
        return queryset
    
    def filter_com_oab(self, queryset, name, value):
        """Filtrar usuários com OAB"""
        if value:
            return queryset.exclude(
                Q(oab_numero__isnull=True) | Q(oab_numero='')
            )
        return queryset
    
    def filter_sem_oab(self, queryset, name, value):
        """Filtrar usuários sem OAB"""
        if value:
            return queryset.filter(
                Q(oab_numero__isnull=True) | Q(oab_numero='')
            )
        return queryset
    
    def filter_online(self, queryset, name, value):
        """Filtrar usuários online (últimos 15 minutos)"""
        if value:
            limite_online = timezone.now() - timedelta(minutes=15)
            return queryset.filter(
                last_login__gte=limite_online,
                is_active=True
            )
        return queryset
    
    def filter_cadastrados_ultima_semana(self, queryset, name, value):
        """Filtrar usuários cadastrados na última semana"""
        if value:
            uma_semana_atras = timezone.now() - timedelta(days=7)
            return queryset.filter(date_joined__gte=uma_semana_atras)
        return queryset
    
    def filter_cadastrados_ultimo_mes(self, queryset, name, value):
        """Filtrar usuários cadastrados no último mês"""
        if value:
            um_mes_atras = timezone.now() - timedelta(days=30)
            return queryset.filter(date_joined__gte=um_mes_atras)
        return queryset
    
    def filter_nunca_logaram(self, queryset, name, value):
        """Filtrar usuários que nunca fizeram login"""
        if value:
            return queryset.filter(last_login__isnull=True)
        return queryset
    
    def filter_com_processos(self, queryset, name, value):
        """Filtrar usuários com processos"""
        if value:
            return queryset.filter(processos_responsavel__isnull=False).distinct()
        return queryset
    
    def filter_sem_processos(self, queryset, name, value):
        """Filtrar usuários sem processos"""
        if value:
            return queryset.filter(processos_responsavel__isnull=True)
        return queryset