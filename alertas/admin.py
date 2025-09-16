from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Alerta, HistoricoAlerta, ConfiguracaoAlerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    """Administração de Alertas"""
    
    list_display = [
        'titulo', 'usuario', 'tipo', 'prioridade_badge', 'status_badge',
        'data_alerta', 'esta_vencido_badge', 'criado_em'
    ]
    
    list_filter = [
        'tipo', 'prioridade', 'status', 'recorrente',
        'criado_em', 'data_alerta'
    ]
    
    search_fields = [
        'titulo', 'descricao', 'usuario__username',
        'usuario__first_name', 'usuario__last_name'
    ]
    
    readonly_fields = [
        'id', 'criado_em', 'atualizado_em', 'concluido_em',
        'tempo_restante_display', 'deve_disparar'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'usuario', 'titulo', 'descricao', 'tipo', 'prioridade', 'status')
        }),
        ('Datas e Horários', {
            'fields': ('data_alerta', 'data_vencimento', 'antecedencia_minutos')
        }),
        ('Recorrência', {
            'fields': ('recorrente', 'frequencia_recorrencia'),
            'classes': ('collapse',)
        }),
        ('Notificações', {
            'fields': ('notificar_email',),
            'classes': ('collapse',)
        }),
        ('Referências', {
            'fields': ('objeto_tipo', 'objeto_id', 'url_acao'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em', 'concluido_em'),
            'classes': ('collapse',)
        }),
        ('Status Atual', {
            'fields': ('tempo_restante_display', 'deve_disparar'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_como_concluido', 'cancelar_alertas', 'reativar_alertas']
    
    def prioridade_badge(self, obj):
        """Exibe a prioridade com badge colorido"""
        cores = {
            'baixa': 'success',
            'media': 'warning', 
            'alta': 'danger',
            'critica': 'dark'
        }
        cor = cores.get(obj.prioridade, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            cor, obj.get_prioridade_display()
        )
    prioridade_badge.short_description = 'Prioridade'
    
    def status_badge(self, obj):
        """Exibe o status com badge colorido"""
        cores = {
            'ativo': 'primary',
            'concluido': 'success',
            'cancelado': 'secondary',
            'adiado': 'warning'
        }
        cor = cores.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def esta_vencido_badge(self, obj):
        """Exibe se o alerta está vencido"""
        if obj.esta_vencido:
            return format_html('<span class="badge bg-danger">Vencido</span>')
        return format_html('<span class="badge bg-success">No Prazo</span>')
    esta_vencido_badge.short_description = 'Situação'
    
    def tempo_restante_display(self, obj):
        """Exibe o tempo restante até o alerta"""
        tempo = obj.tempo_restante
        if tempo:
            dias = tempo.days
            horas = tempo.seconds // 3600
            minutos = (tempo.seconds % 3600) // 60
            
            if dias > 0:
                return f'{dias} dias, {horas}h {minutos}min'
            elif horas > 0:
                return f'{horas}h {minutos}min'
            else:
                return f'{minutos}min'
        return 'Vencido'
    tempo_restante_display.short_description = 'Tempo Restante'
    
    def marcar_como_concluido(self, request, queryset):
        """Marca alertas selecionados como concluídos"""
        count = 0
        for alerta in queryset:
            if alerta.status == 'ativo':
                alerta.marcar_como_concluido()
                count += 1
        
        self.message_user(
            request,
            f'{count} alerta(s) marcado(s) como concluído(s).'
        )
    marcar_como_concluido.short_description = 'Marcar como concluído'
    
    def cancelar_alertas(self, request, queryset):
        """Cancela alertas selecionados"""
        count = 0
        for alerta in queryset:
            if alerta.status in ['ativo', 'adiado']:
                alerta.cancelar()
                count += 1
        
        self.message_user(
            request,
            f'{count} alerta(s) cancelado(s).'
        )
    cancelar_alertas.short_description = 'Cancelar alertas'
    
    def reativar_alertas(self, request, queryset):
        """Reativa alertas cancelados"""
        count = queryset.filter(status='cancelado').update(status='ativo')
        self.message_user(
            request,
            f'{count} alerta(s) reativado(s).'
        )
    reativar_alertas.short_description = 'Reativar alertas'


class HistoricoAlertaInline(admin.TabularInline):
    """Inline para histórico de alertas"""
    model = HistoricoAlerta
    extra = 0
    readonly_fields = ['acao', 'descricao', 'usuario', 'data_acao']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(HistoricoAlerta)
class HistoricoAlertaAdmin(admin.ModelAdmin):
    """Administração do Histórico de Alertas"""
    
    list_display = [
        'alerta', 'acao', 'usuario', 'data_acao'
    ]
    
    list_filter = [
        'acao', 'data_acao'
    ]
    
    search_fields = [
        'alerta__titulo', 'descricao', 'usuario__username'
    ]
    
    readonly_fields = [
        'alerta', 'acao', 'descricao', 'usuario', 'data_acao'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracaoAlerta)
class ConfiguracaoAlertaAdmin(admin.ModelAdmin):
    """Administração das Configurações de Alertas"""
    
    list_display = [
        'usuario', 'alertas_ativos', 'notificacao_email',
        'antecedencia_padrao', 'atualizado_em'
    ]
    
    list_filter = [
        'alertas_ativos', 'notificacao_email', 'notificacao_push',
        'alertas_fins_semana'
    ]
    
    search_fields = [
        'usuario__username', 'usuario__first_name', 'usuario__last_name'
    ]
    
    fieldsets = (
        ('Usuário', {
            'fields': ('usuario',)
        }),
        ('Configurações Gerais', {
            'fields': ('alertas_ativos', 'antecedencia_padrao')
        }),
        ('Tipos de Alertas', {
            'fields': (
                'alertas_prazos', 'alertas_audiencias', 'alertas_reunioes',
                'alertas_pagamentos', 'alertas_tarefas'
            )
        }),
        ('Notificações', {
            'fields': ('notificacao_email', 'notificacao_push')
        }),
        ('Horários', {
            'fields': ('horario_inicio', 'horario_fim', 'alertas_fins_semana')
        }),
    )
    
    readonly_fields = ['criado_em', 'atualizado_em']