import django_filters
from django.db.models import Q
from django.utils import timezone
from django import forms
from datetime import timedelta
from .models import Cliente


class ClienteFilter(django_filters.FilterSet):
    """Filtros para clientes"""
    
    # Busca geral em múltiplos campos
    search = django_filters.CharFilter(
        method='filter_search',
        widget=forms.TextInput(attrs={
            'class': 'form-control search-box',
            'placeholder': 'Nome, CPF/CNPJ, email ou telefone...'
        }),
        label='Buscar'
    )
    
    # Filtros básicos
    nome_razao_social = django_filters.CharFilter(
        field_name='nome_razao_social',
        lookup_expr='icontains',
        label='Nome/Razão Social',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    tipo_pessoa = django_filters.ChoiceFilter(
        choices=[('', 'Todos')] + Cliente.TIPO_PESSOA_CHOICES,
        label='Tipo de Pessoa',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cpf_cnpj = django_filters.CharFilter(
        field_name='cpf_cnpj',
        lookup_expr='icontains',
        label='CPF/CNPJ',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='E-mail',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    telefone = django_filters.CharFilter(
        field_name='telefone',
        lookup_expr='icontains',
        label='Telefone',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Filtros por localização
    cidade = django_filters.CharFilter(
        field_name='cidade',
        lookup_expr='icontains',
        label='Cidade',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    uf = django_filters.ChoiceFilter(
        choices=[('', 'Todos')] + [
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
        label='Estado (UF)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cep = django_filters.CharFilter(
        field_name='cep',
        lookup_expr='icontains',
        label='CEP',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Filtro por status
    ativo = django_filters.BooleanFilter(
        field_name='ativo',
        label='Ativo',
        widget=forms.Select(
            choices=[('', 'Todos'), (True, 'Ativo'), (False, 'Inativo')],
            attrs={'class': 'form-select'}
        )
    )
    
    # Filtros por data
    data_nascimento_fundacao = django_filters.DateFilter(
        field_name='data_nascimento_fundacao',
        label='Data de Nascimento/Fundação'
    )
    
    data_nascimento_fundacao_after = django_filters.DateFilter(
        field_name='data_nascimento_fundacao',
        lookup_expr='gte',
        label='Data de Nascimento/Fundação (a partir de)'
    )
    
    data_nascimento_fundacao_before = django_filters.DateFilter(
        field_name='data_nascimento_fundacao',
        lookup_expr='lte',
        label='Data de Nascimento/Fundação (até)'
    )
    
    # Filtros especiais
    com_processos = django_filters.BooleanFilter(
        method='filter_com_processos',
        label='Com Processos'
    )
    
    sem_processos = django_filters.BooleanFilter(
        method='filter_sem_processos',
        label='Sem Processos'
    )
    
    com_processos_ativos = django_filters.BooleanFilter(
        method='filter_com_processos_ativos',
        label='Com Processos Ativos'
    )
    
    criados_ultima_semana = django_filters.BooleanFilter(
        method='filter_criados_ultima_semana',
        label='Criados na Última Semana'
    )
    
    criados_ultimo_mes = django_filters.BooleanFilter(
        method='filter_criados_ultimo_mes',
        label='Criados no Último Mês'
    )
    
    # Filtro por profissão/atividade
    profissao_atividade = django_filters.CharFilter(
        field_name='profissao_atividade',
        lookup_expr='icontains',
        label='Profissão/Atividade'
    )
    
    # Filtro por estado civil (apenas para PF)
    estado_civil = django_filters.ChoiceFilter(
        choices=[
            ('solteiro', 'Solteiro(a)'),
            ('casado', 'Casado(a)'),
            ('divorciado', 'Divorciado(a)'),
            ('viuvo', 'Viúvo(a)'),
            ('separado', 'Separado(a)'),
            ('uniao_estavel', 'União Estável')
        ],
        label='Estado Civil'
    )
    
    # Filtro por nacionalidade
    nacionalidade = django_filters.CharFilter(
        field_name='nacionalidade',
        lookup_expr='icontains',
        label='Nacionalidade'
    )
    
    class Meta:
        model = Cliente
        fields = [
            'nome_razao_social', 'tipo_pessoa', 'cpf_cnpj', 'email',
            'telefone', 'cidade', 'uf', 'cep', 'ativo',
            'data_nascimento_fundacao', 'profissao_atividade',
            'estado_civil', 'nacionalidade'
        ]
    
    def filter_search(self, queryset, name, value):
        """
        Filtro personalizado para busca em múltiplos campos.
        Busca por nome, CPF/CNPJ, email ou telefone.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(nome_razao_social__icontains=value) |
            Q(cpf_cnpj__icontains=value) |
            Q(email__icontains=value) |
            Q(telefone__icontains=value)
        )

    def filter_com_processos(self, queryset, name, value):
        """Filtrar clientes com processos"""
        if value:
            return queryset.filter(processos__isnull=False).distinct()
        return queryset
    
    def filter_sem_processos(self, queryset, name, value):
        """Filtrar clientes sem processos"""
        if value:
            return queryset.filter(processos__isnull=True)
        return queryset
    
    def filter_com_processos_ativos(self, queryset, name, value):
        """Filtrar clientes com processos ativos"""
        if value:
            return queryset.filter(
                processos__status='ativo'
            ).distinct()
        return queryset
    
    def filter_criados_ultima_semana(self, queryset, name, value):
        """Filtrar clientes criados na última semana"""
        if value:
            uma_semana_atras = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=uma_semana_atras)
        return queryset
    
    def filter_criados_ultimo_mes(self, queryset, name, value):
        """Filtrar clientes criados no último mês"""
        if value:
            um_mes_atras = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=um_mes_atras)
        return queryset