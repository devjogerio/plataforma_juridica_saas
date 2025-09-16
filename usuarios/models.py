import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Usuario(AbstractUser):
    """
    Modelo de usuário personalizado para a plataforma jurídica.
    Estende o modelo AbstractUser do Django com campos específicos.
    """
    
    TIPO_USUARIO_CHOICES = [
        ('administrador', _('Administrador')),
        ('advogado', _('Advogado')),
        ('estagiario', _('Estagiário')),
        ('cliente', _('Cliente')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do usuário')
    )
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='advogado',
        verbose_name=_('Tipo de Usuário'),
        help_text=_('Define o perfil e permissões do usuário no sistema')
    )
    
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Telefone'),
        help_text=_('Número de telefone para contato')
    )
    
    oab_numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Número OAB'),
        help_text=_('Número de registro na OAB (apenas para advogados)')
    )
    
    oab_uf = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name=_('UF OAB'),
        help_text=_('Estado de registro na OAB')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Data de Atualização')
    )
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['first_name', 'last_name']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_tipo_usuario_display()})"
    
    def get_full_name(self):
        """Retorna o nome completo do usuário."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_advogado(self):
        """Verifica se o usuário é advogado."""
        return self.tipo_usuario == 'advogado'
    
    @property
    def is_administrador(self):
        """Verifica se o usuário é administrador."""
        return self.tipo_usuario == 'administrador'
    
    @property
    def is_estagiario(self):
        """Verifica se o usuário é estagiário."""
        return self.tipo_usuario == 'estagiario'
    
    @property
    def is_cliente(self):
        """Verifica se o usuário é cliente."""
        return self.tipo_usuario == 'cliente'
    
    def get_preferencias(self):
        """Retorna as preferências do usuário, criando se não existir."""
        preferencias, created = PreferenciaUsuario.objects.get_or_create(usuario=self)
        return preferencias


class Permissao(models.Model):
    """
    Modelo para controle granular de permissões por usuário.
    Implementa RBAC (Role-Based Access Control).
    """
    
    MODULO_CHOICES = [
        ('processos', _('Processos')),
        ('clientes', _('Clientes')),
        ('documentos', _('Documentos')),
        ('financeiro', _('Financeiro')),
        ('relatorios', _('Relatórios')),
        ('configuracoes', _('Configurações')),
        ('usuarios', _('Usuários')),
    ]
    
    ACAO_CHOICES = [
        ('create', _('Criar')),
        ('read', _('Visualizar')),
        ('update', _('Editar')),
        ('delete', _('Excluir')),
        ('export', _('Exportar')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='permissoes_customizadas',
        verbose_name=_('Usuário')
    )
    
    modulo = models.CharField(
        max_length=20,
        choices=MODULO_CHOICES,
        verbose_name=_('Módulo')
    )
    
    acao = models.CharField(
        max_length=10,
        choices=ACAO_CHOICES,
        verbose_name=_('Ação')
    )
    
    permitido = models.BooleanField(
        default=True,
        verbose_name=_('Permitido'),
        help_text=_('Define se a ação é permitida ou negada')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Permissão')
        verbose_name_plural = _('Permissões')
        unique_together = ['usuario', 'modulo', 'acao']
        ordering = ['usuario', 'modulo', 'acao']
    
    def __str__(self):
        status = 'Permitido' if self.permitido else 'Negado'
        return f"{self.usuario.username} - {self.get_modulo_display()}: {self.get_acao_display()} ({status})"


class AuditLog(models.Model):
    """
    Modelo para auditoria de ações dos usuários no sistema.
    Registra todas as operações importantes para compliance.
    """
    
    ACAO_CHOICES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('create', _('Criação')),
        ('update', _('Atualização')),
        ('delete', _('Exclusão')),
        ('view', _('Visualização')),
        ('export', _('Exportação')),
        ('upload', _('Upload')),
        ('download', _('Download')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Usuário')
    )
    
    acao = models.CharField(
        max_length=20,
        choices=ACAO_CHOICES,
        verbose_name=_('Ação')
    )
    
    modelo = models.CharField(
        max_length=100,
        verbose_name=_('Modelo'),
        help_text=_('Nome do modelo afetado')
    )
    
    objeto_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('ID do Objeto'),
        help_text=_('Identificador do objeto afetado')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=_('Endereço IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User Agent')
    )
    
    detalhes = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Detalhes'),
        help_text=_('Informações adicionais sobre a ação')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data/Hora')
    )
    
    class Meta:
        verbose_name = _('Log de Auditoria')
        verbose_name_plural = _('Logs de Auditoria')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['acao', '-timestamp']),
            models.Index(fields=['modelo', '-timestamp']),
        ]
    
    def __str__(self):
        usuario_nome = self.usuario.username if self.usuario else 'Anônimo'
        return f"{usuario_nome} - {self.get_acao_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class PreferenciaUsuario(models.Model):
    """
    Modelo para armazenar preferências personalizadas do usuário.
    Inclui configurações de tema, idioma, notificações e interface.
    """
    
    TEMA_CHOICES = [
        ('light', _('Claro')),
        ('dark', _('Escuro')),
        ('auto', _('Automático')),
    ]
    
    IDIOMA_CHOICES = [
        ('pt-br', _('Português (Brasil)')),
        ('en', _('English')),
        ('es', _('Español')),
    ]
    
    TIMEZONE_CHOICES = [
        ('America/Sao_Paulo', _('São Paulo (GMT-3)')),
        ('America/Manaus', _('Manaus (GMT-4)')),
        ('America/Rio_Branco', _('Rio Branco (GMT-5)')),
    ]
    
    ITEMS_POR_PAGINA_CHOICES = [
        (10, '10 itens'),
        (20, '20 itens'),
        (50, '50 itens'),
        (100, '100 itens'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='preferencias',
        verbose_name=_('Usuário')
    )
    
    # Configurações de Interface
    tema = models.CharField(
        max_length=10,
        choices=TEMA_CHOICES,
        default='light',
        verbose_name=_('Tema'),
        help_text=_('Tema da interface do usuário')
    )
    
    idioma = models.CharField(
        max_length=10,
        choices=IDIOMA_CHOICES,
        default='pt-br',
        verbose_name=_('Idioma'),
        help_text=_('Idioma da interface')
    )
    
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/Sao_Paulo',
        verbose_name=_('Fuso Horário'),
        help_text=_('Fuso horário para exibição de datas e horários')
    )
    
    items_por_pagina = models.IntegerField(
        choices=ITEMS_POR_PAGINA_CHOICES,
        default=20,
        verbose_name=_('Itens por Página'),
        help_text=_('Número de itens exibidos por página nas listagens')
    )
    
    # Configurações de Notificações
    notificacoes_email = models.BooleanField(
        default=True,
        verbose_name=_('Notificações por E-mail'),
        help_text=_('Receber notificações por e-mail')
    )
    
    notificacoes_prazos = models.BooleanField(
        default=True,
        verbose_name=_('Alertas de Prazos'),
        help_text=_('Receber alertas sobre prazos próximos')
    )
    
    notificacoes_sistema = models.BooleanField(
        default=True,
        verbose_name=_('Notificações do Sistema'),
        help_text=_('Receber notificações sobre atualizações do sistema')
    )
    
    notificacoes_marketing = models.BooleanField(
        default=False,
        verbose_name=_('E-mails Promocionais'),
        help_text=_('Receber e-mails promocionais e newsletters')
    )
    
    # Configurações de Dashboard
    dashboard_widgets = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Widgets do Dashboard'),
        help_text=_('Configuração dos widgets exibidos no dashboard')
    )
    
    sidebar_collapsed = models.BooleanField(
        default=False,
        verbose_name=_('Sidebar Recolhida'),
        help_text=_('Define se a sidebar deve iniciar recolhida')
    )
    
    # Configurações de Relatórios
    formato_data_preferido = models.CharField(
        max_length=20,
        choices=[
            ('dd/mm/yyyy', 'DD/MM/AAAA'),
            ('mm/dd/yyyy', 'MM/DD/AAAA'),
            ('yyyy-mm-dd', 'AAAA-MM-DD'),
        ],
        default='dd/mm/yyyy',
        verbose_name=_('Formato de Data Preferido')
    )
    
    formato_moeda_preferido = models.CharField(
        max_length=10,
        choices=[
            ('BRL', 'Real (R$)'),
            ('USD', 'Dólar ($)'),
            ('EUR', 'Euro (€)'),
        ],
        default='BRL',
        verbose_name=_('Formato de Moeda Preferido')
    )
    
    # Metadados
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Data de Atualização')
    )
    
    class Meta:
        verbose_name = _('Preferência do Usuário')
        verbose_name_plural = _('Preferências dos Usuários')
        ordering = ['usuario__first_name', 'usuario__last_name']
    
    def __str__(self):
        return f"Preferências de {self.usuario.get_full_name()}"
    
    def get_dashboard_widgets_default(self):
        """Retorna configuração padrão dos widgets do dashboard."""
        return {
            'processos_recentes': {'enabled': True, 'order': 1},
            'prazos_proximos': {'enabled': True, 'order': 2},
            'estatisticas_gerais': {'enabled': True, 'order': 3},
            'grafico_processos': {'enabled': True, 'order': 4},
            'atividades_recentes': {'enabled': True, 'order': 5},
            'clientes_ativos': {'enabled': True, 'order': 6},
        }
    
    def save(self, *args, **kwargs):
        # Definir widgets padrão se não existirem
        if not self.dashboard_widgets:
            self.dashboard_widgets = self.get_dashboard_widgets_default()
        super().save(*args, **kwargs)
