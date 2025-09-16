from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Notificacao, ConfiguracaoNotificacao, TipoNotificacao, PrioridadeNotificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    """Admin para notificações"""
    
    list_display = [
        'titulo',
        'usuario_display',
        'tipo_display',
        'prioridade_display',
        'lida_display',
        'criada_em',
        'acoes'
    ]
    
    list_filter = [
        'tipo',
        'prioridade',
        'lida',
        'criada_em',
        'lida_em'
    ]
    
    search_fields = [
        'titulo',
        'mensagem',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name'
    ]
    
    readonly_fields = [
        'criada_em',
        'lida_em',
        'tempo_desde_criacao'
    ]
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': [
                'usuario',
                'titulo',
                'mensagem',
                'tipo',
                'prioridade'
            ]
        }),
        ('Status', {
            'fields': [
                'lida',
                'lida_em'
            ]
        }),
        ('Metadados', {
            'fields': [
                'url_acao',
                'icone',
                'objeto_tipo',
                'objeto_id',
                'expira_em'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': [
                'criada_em',
                'tempo_desde_criacao'
            ],
            'classes': ['collapse']
        })
    ]
    
    date_hierarchy = 'criada_em'
    
    def usuario_display(self, obj):
        """Exibe o usuário com link"""
        if obj.usuario:
            url = reverse('admin:auth_user_change', args=[obj.usuario.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.usuario.get_full_name() or obj.usuario.username
            )
        return '-'
    usuario_display.short_description = 'Usuário'
    
    def tipo_display(self, obj):
        """Exibe o tipo com ícone e cor"""
        icone = obj.get_icone_classe()
        cor = obj.get_cor_classe()
        
        return format_html(
            '<i class="{} {}"></i> {}',
            icone,
            cor,
            obj.get_tipo_display()
        )
    tipo_display.short_description = 'Tipo'
    
    def prioridade_display(self, obj):
        """Exibe a prioridade com cor"""
        cores = {
            PrioridadeNotificacao.BAIXA: 'success',
            PrioridadeNotificacao.MEDIA: 'info',
            PrioridadeNotificacao.ALTA: 'warning',
            PrioridadeNotificacao.CRITICA: 'danger'
        }
        
        cor = cores.get(obj.prioridade, 'secondary')
        
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            cor,
            obj.get_prioridade_display()
        )
    prioridade_display.short_description = 'Prioridade'
    
    def lida_display(self, obj):
        """Exibe status de leitura"""
        if obj.lida:
            return format_html(
                '<span class="badge badge-success">✓ Lida</span>'
            )
        else:
            return format_html(
                '<span class="badge badge-warning">✗ Não lida</span>'
            )
    lida_display.short_description = 'Status'
    
    def acoes(self, obj):
        """Ações disponíveis"""
        acoes_html = []
        
        if not obj.lida:
            acoes_html.append(
                '<a href="#" onclick="marcarComoLida({}); return false;" '
                'class="btn btn-sm btn-success">Marcar como Lida</a>'.format(obj.pk)
            )
        
        if obj.url_acao:
            acoes_html.append(
                '<a href="{}" target="_blank" '
                'class="btn btn-sm btn-primary">Ver Ação</a>'.format(obj.url_acao)
            )
        
        return format_html(' '.join(acoes_html))
    acoes.short_description = 'Ações'
    
    def tempo_desde_criacao(self, obj):
        """Calcula tempo desde a criação"""
        if obj.criada_em:
            agora = timezone.now()
            diferenca = agora - obj.criada_em
            
            if diferenca.days > 0:
                return f'{diferenca.days} dia(s) atrás'
            elif diferenca.seconds > 3600:
                horas = diferenca.seconds // 3600
                return f'{horas} hora(s) atrás'
            elif diferenca.seconds > 60:
                minutos = diferenca.seconds // 60
                return f'{minutos} minuto(s) atrás'
            else:
                return 'Agora mesmo'
        return '-'
    tempo_desde_criacao.short_description = 'Tempo desde criação'
    
    def get_queryset(self, request):
        """Otimiza queryset"""
        return super().get_queryset(request).select_related('usuario')
    
    class Media:
        js = [
            'admin/js/notificacao_admin.js'
        ]


@admin.register(ConfiguracaoNotificacao)
class ConfiguracaoNotificacaoAdmin(admin.ModelAdmin):
    """Admin para configurações de notificação"""
    
    list_display = [
        'usuario_display',
        'prazo_critico',
        'novo_andamento',
        'documento_upload',
        'financeiro',
        'sistema',
        'email_enabled',
        'dias_antecedencia'
    ]
    
    list_filter = [
        'receber_prazo_critico',
        'receber_novo_andamento',
        'receber_documento_upload',
        'receber_financeiro',
        'receber_sistema',
        'notificacao_email'
    ]
    
    search_fields = [
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name'
    ]
    
    fieldsets = [
        ('Usuário', {
            'fields': ['usuario']
        }),
        ('Tipos de Notificação', {
            'fields': [
                'receber_prazo_critico',
                'receber_novo_andamento',
                'receber_documento_upload',
                'receber_financeiro',
                'receber_sistema'
            ]
        }),
        ('Configurações de Entrega', {
            'fields': [
                'notificacao_email',
                'dias_antecedencia_prazo'
            ]
        })
    ]
    
    def usuario_display(self, obj):
        """Exibe o usuário"""
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '-'
    usuario_display.short_description = 'Usuário'
    
    def prazo_critico(self, obj):
        return '✓' if obj.receber_prazo_critico else '✗'
    prazo_critico.short_description = 'Prazo Crítico'
    prazo_critico.boolean = True
    
    def novo_andamento(self, obj):
        return '✓' if obj.receber_novo_andamento else '✗'
    novo_andamento.short_description = 'Novo Andamento'
    novo_andamento.boolean = True
    
    def documento_upload(self, obj):
        return '✓' if obj.receber_documento_upload else '✗'
    documento_upload.short_description = 'Upload Documento'
    documento_upload.boolean = True
    
    def financeiro(self, obj):
        return '✓' if obj.receber_financeiro else '✗'
    financeiro.short_description = 'Financeiro'
    financeiro.boolean = True
    
    def sistema(self, obj):
        return '✓' if obj.receber_sistema else '✗'
    sistema.short_description = 'Sistema'
    sistema.boolean = True
    
    def email_enabled(self, obj):
        return '✓' if obj.notificacao_email else '✗'
    email_enabled.short_description = 'Email'
    email_enabled.boolean = True
    
    def dias_antecedencia(self, obj):
        return f'{obj.dias_antecedencia_prazo} dias'
    dias_antecedencia.short_description = 'Antecedência'


# Customização do admin site
admin.site.site_header = 'Plataforma Jurídica - Administração'
admin.site.site_title = 'Plataforma Jurídica'
admin.site.index_title = 'Painel de Administração'
