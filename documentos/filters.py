import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Documento, TipoDocumento
from processos.models import Processo
from django.contrib.auth import get_user_model

User = get_user_model()


class DocumentoFilter(django_filters.FilterSet):
    """Filtros para documentos"""
    
    # Filtros básicos
    nome_arquivo = django_filters.CharFilter(
        field_name='nome_arquivo',
        lookup_expr='icontains',
        label='Nome do Arquivo'
    )
    
    tipo_documento = django_filters.ModelChoiceFilter(
        queryset=TipoDocumento.objects.filter(ativo=True),
        label='Tipo de Documento'
    )
    
    processo = django_filters.ModelChoiceFilter(
        queryset=Processo.objects.all(),
        label='Processo'
    )
    
    processo_numero = django_filters.CharFilter(
        field_name='processo__numero_processo',
        lookup_expr='icontains',
        label='Número do Processo'
    )
    
    usuario_upload = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(is_active=True),
        label='Usuário que fez Upload'
    )
    
    # Filtros por data
    data_upload = django_filters.DateFilter(
        field_name='data_upload',
        label='Data de Upload'
    )
    
    data_upload_after = django_filters.DateFilter(
        field_name='data_upload',
        lookup_expr='gte',
        label='Data de Upload (a partir de)'
    )
    
    data_upload_before = django_filters.DateFilter(
        field_name='data_upload',
        lookup_expr='lte',
        label='Data de Upload (até)'
    )
    
    # Filtros por tamanho
    tamanho_min = django_filters.NumberFilter(
        method='filter_tamanho_min',
        label='Tamanho Mínimo (bytes)'
    )
    
    tamanho_max = django_filters.NumberFilter(
        method='filter_tamanho_max',
        label='Tamanho Máximo (bytes)'
    )
    
    # Filtros por extensão
    extensao = django_filters.CharFilter(
        method='filter_extensao',
        label='Extensão do Arquivo'
    )
    
    # Filtros por status
    confidencial = django_filters.BooleanFilter(
        field_name='confidencial',
        label='Confidencial'
    )
    
    ativo = django_filters.BooleanFilter(
        field_name='ativo',
        label='Ativo'
    )
    
    # Filtros por versão
    versao = django_filters.NumberFilter(
        field_name='versao',
        label='Versão'
    )
    
    versao_min = django_filters.NumberFilter(
        field_name='versao',
        lookup_expr='gte',
        label='Versão Mínima'
    )
    
    versao_max = django_filters.NumberFilter(
        field_name='versao',
        lookup_expr='lte',
        label='Versão Máxima'
    )
    
    # Filtros especiais
    sem_processo = django_filters.BooleanFilter(
        method='filter_sem_processo',
        label='Sem Processo Vinculado'
    )
    
    com_multiplas_versoes = django_filters.BooleanFilter(
        method='filter_com_multiplas_versoes',
        label='Com Múltiplas Versões'
    )
    
    upload_ultima_semana = django_filters.BooleanFilter(
        method='filter_upload_ultima_semana',
        label='Upload na Última Semana'
    )
    
    upload_ultimo_mes = django_filters.BooleanFilter(
        method='filter_upload_ultimo_mes',
        label='Upload no Último Mês'
    )
    
    apenas_versao_atual = django_filters.BooleanFilter(
        method='filter_apenas_versao_atual',
        label='Apenas Versão Atual'
    )
    
    # Filtros por tipo de arquivo
    tipo_arquivo = django_filters.ChoiceFilter(
        method='filter_tipo_arquivo',
        choices=[
            ('pdf', 'PDF'),
            ('word', 'Word (DOC/DOCX)'),
            ('excel', 'Excel (XLS/XLSX)'),
            ('imagem', 'Imagem (JPG/PNG)'),
            ('texto', 'Texto (TXT/RTF)'),
            ('outros', 'Outros')
        ],
        label='Tipo de Arquivo'
    )
    
    # Filtro por cliente (através do processo)
    cliente = django_filters.CharFilter(
        field_name='processo__cliente__nome_razao_social',
        lookup_expr='icontains',
        label='Cliente'
    )
    
    # Filtro por área do direito (através do processo)
    area_direito = django_filters.ChoiceFilter(
        field_name='processo__area_direito',
        choices=Processo.AREA_DIREITO_CHOICES,
        label='Área do Direito'
    )
    
    # Filtros por status e confidencialidade
    status = django_filters.ChoiceFilter(
        choices=Documento.STATUS_CHOICES,
        label='Status'
    )
    
    confidencialidade = django_filters.ChoiceFilter(
        choices=Documento.CONFIDENCIALIDADE_CHOICES,
        label='Confidencialidade'
    )
    
    class Meta:
        model = Documento
        fields = [
            'nome_arquivo', 'tipo_documento', 'processo', 'usuario_upload',
            'status', 'confidencialidade', 'versao', 'extensao'
        ]
    
    def filter_tamanho_min(self, queryset, name, value):
        """Filtrar por tamanho mínimo do arquivo"""
        if value:
            return queryset.filter(arquivo__size__gte=value)
        return queryset
    
    def filter_tamanho_max(self, queryset, name, value):
        """Filtrar por tamanho máximo do arquivo"""
        if value:
            return queryset.filter(arquivo__size__lte=value)
        return queryset
    
    def filter_extensao(self, queryset, name, value):
        """Filtrar por extensão do arquivo"""
        if value:
            return queryset.filter(arquivo__name__iendswith=f'.{value}')
        return queryset
    
    def filter_sem_processo(self, queryset, name, value):
        """Filtrar documentos sem processo vinculado"""
        if value:
            return queryset.filter(processo__isnull=True)
        return queryset
    
    def filter_com_multiplas_versoes(self, queryset, name, value):
        """Filtrar documentos com múltiplas versões"""
        if value:
            # Documentos que são pai de outros ou que têm pai
            return queryset.filter(
                Q(versoes__isnull=False) | Q(documento_pai__isnull=False)
            ).distinct()
        return queryset
    
    def filter_upload_ultima_semana(self, queryset, name, value):
        """Filtrar documentos enviados na última semana"""
        if value:
            uma_semana_atras = timezone.now() - timedelta(days=7)
            return queryset.filter(data_upload__gte=uma_semana_atras)
        return queryset
    
    def filter_upload_ultimo_mes(self, queryset, name, value):
        """Filtrar documentos enviados no último mês"""
        if value:
            um_mes_atras = timezone.now() - timedelta(days=30)
            return queryset.filter(data_upload__gte=um_mes_atras)
        return queryset
    
    def filter_apenas_versao_atual(self, queryset, name, value):
        """Filtrar apenas versões atuais (não versões antigas)"""
        if value:
            # Documentos que não têm pai (são a versão principal)
            # ou que são a versão mais recente de um documento
            return queryset.filter(
                Q(documento_pai__isnull=True) |
                Q(documento_pai__isnull=False, versao__in=
                  queryset.filter(
                      documento_pai=models.OuterRef('documento_pai')
                  ).aggregate(max_versao=models.Max('versao'))['max_versao']
                )
            )
        return queryset
    
    def filter_tipo_arquivo(self, queryset, name, value):
        """Filtrar por tipo de arquivo baseado na extensão"""
        if value == 'pdf':
            return queryset.filter(arquivo__name__iendswith='.pdf')
        elif value == 'word':
            return queryset.filter(
                Q(arquivo__name__iendswith='.doc') |
                Q(arquivo__name__iendswith='.docx')
            )
        elif value == 'excel':
            return queryset.filter(
                Q(arquivo__name__iendswith='.xls') |
                Q(arquivo__name__iendswith='.xlsx')
            )
        elif value == 'imagem':
            return queryset.filter(
                Q(arquivo__name__iendswith='.jpg') |
                Q(arquivo__name__iendswith='.jpeg') |
                Q(arquivo__name__iendswith='.png')
            )
        elif value == 'texto':
            return queryset.filter(
                Q(arquivo__name__iendswith='.txt') |
                Q(arquivo__name__iendswith='.rtf')
            )
        elif value == 'outros':
            # Excluir os tipos conhecidos
            return queryset.exclude(
                Q(arquivo__name__iendswith='.pdf') |
                Q(arquivo__name__iendswith='.doc') |
                Q(arquivo__name__iendswith='.docx') |
                Q(arquivo__name__iendswith='.xls') |
                Q(arquivo__name__iendswith='.xlsx') |
                Q(arquivo__name__iendswith='.jpg') |
                Q(arquivo__name__iendswith='.jpeg') |
                Q(arquivo__name__iendswith='.png') |
                Q(arquivo__name__iendswith='.txt') |
                Q(arquivo__name__iendswith='.rtf')
            )
        
        return queryset