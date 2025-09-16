import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

User = get_user_model()


class TemplateRelatorio(models.Model):
    """
    Modelo para templates de relatórios personalizáveis.
    Permite criar relatórios reutilizáveis com configurações específicas.
    """
    
    TIPO_RELATORIO_CHOICES = [
        ('processos', _('Relatório de Processos')),
        ('clientes', _('Relatório de Clientes')),
        ('financeiro', _('Relatório Financeiro')),
        ('produtividade', _('Relatório de Produtividade')),
        ('prazos', _('Relatório de Prazos')),
        ('documentos', _('Relatório de Documentos')),
        ('personalizado', _('Relatório Personalizado')),
    ]
    
    FORMATO_SAIDA_CHOICES = [
        ('pdf', _('PDF')),
        ('excel', _('Excel')),
        ('csv', _('CSV')),
        ('html', _('HTML')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome = models.CharField(
        max_length=200,
        verbose_name=_('Nome do Template'),
        help_text=_('Nome identificador do template de relatório')
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição detalhada do que o relatório apresenta')
    )
    
    tipo_relatorio = models.CharField(
        max_length=20,
        choices=TIPO_RELATORIO_CHOICES,
        verbose_name=_('Tipo de Relatório')
    )
    
    formato_saida = models.CharField(
        max_length=10,
        choices=FORMATO_SAIDA_CHOICES,
        default='pdf',
        verbose_name=_('Formato de Saída')
    )
    
    campos_selecionados = models.JSONField(
        default=list,
        verbose_name=_('Campos Selecionados'),
        help_text=_('Lista de campos que serão incluídos no relatório')
    )
    
    filtros_padrao = models.JSONField(
        default=dict,
        verbose_name=_('Filtros Padrão'),
        help_text=_('Filtros que serão aplicados por padrão no relatório')
    )
    
    ordenacao_padrao = models.JSONField(
        default=list,
        verbose_name=_('Ordenação Padrão'),
        help_text=_('Campos e direção de ordenação padrão')
    )
    
    agrupamento = models.JSONField(
        default=list,
        verbose_name=_('Agrupamento'),
        help_text=_('Campos para agrupamento de dados')
    )
    
    configuracoes_layout = models.JSONField(
        default=dict,
        verbose_name=_('Configurações de Layout'),
        help_text=_('Configurações visuais do relatório (cores, fontes, etc.)')
    )
    
    publico = models.BooleanField(
        default=False,
        verbose_name=_('Público'),
        help_text=_('Se marcado, o template estará disponível para todos os usuários')
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
    )
    
    usuario_criador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='templates_relatorio',
        verbose_name=_('Usuário Criador')
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
        verbose_name = _('Template de Relatório')
        verbose_name_plural = _('Templates de Relatórios')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['tipo_relatorio']),
            models.Index(fields=['usuario_criador']),
            models.Index(fields=['publico', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_relatorio_display()})"
    
    @property
    def total_execucoes(self):
        """Retorna o total de execuções deste template."""
        return self.execucoes.count()
    
    @property
    def ultima_execucao(self):
        """Retorna a data da última execução."""
        ultima = self.execucoes.order_by('-data_execucao').first()
        return ultima.data_execucao if ultima else None


class ExecucaoRelatorio(models.Model):
    """
    Modelo para registrar execuções de relatórios.
    Mantém histórico de quando e por quem os relatórios foram gerados.
    """
    
    STATUS_CHOICES = [
        ('processando', _('Processando')),
        ('concluido', _('Concluído')),
        ('erro', _('Erro')),
        ('cancelado', _('Cancelado')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    template = models.ForeignKey(
        TemplateRelatorio,
        on_delete=models.CASCADE,
        related_name='execucoes',
        verbose_name=_('Template')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='execucoes_relatorio',
        verbose_name=_('Usuário')
    )
    
    parametros_execucao = models.JSONField(
        default=dict,
        verbose_name=_('Parâmetros de Execução'),
        help_text=_('Filtros e parâmetros específicos desta execução')
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='processando',
        verbose_name=_('Status')
    )
    
    data_execucao = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Execução')
    )
    
    data_conclusao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Data de Conclusão')
    )
    
    tempo_processamento = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_('Tempo de Processamento')
    )
    
    total_registros = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Total de Registros'),
        help_text=_('Quantidade de registros incluídos no relatório')
    )
    
    tamanho_arquivo = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Tamanho do Arquivo (bytes)')
    )
    
    caminho_arquivo = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Caminho do Arquivo'),
        help_text=_('Caminho onde o arquivo foi salvo')
    )
    
    mensagem_erro = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Mensagem de Erro')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    class Meta:
        verbose_name = _('Execução de Relatório')
        verbose_name_plural = _('Execuções de Relatórios')
        ordering = ['-data_execucao']
        indexes = [
            models.Index(fields=['template', '-data_execucao']),
            models.Index(fields=['usuario', '-data_execucao']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.template.nome} - {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def tamanho_arquivo_formatado(self):
        """Retorna o tamanho do arquivo formatado."""
        if not self.tamanho_arquivo:
            return '-'
        
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} bytes"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"


class DashboardPersonalizado(models.Model):
    """
    Modelo para dashboards personalizados.
    Permite criar dashboards com widgets específicos para cada usuário.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome = models.CharField(
        max_length=200,
        verbose_name=_('Nome do Dashboard')
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição')
    )
    
    configuracao_widgets = models.JSONField(
        default=list,
        verbose_name=_('Configuração dos Widgets'),
        help_text=_('Lista de widgets e suas configurações')
    )
    
    layout = models.JSONField(
        default=dict,
        verbose_name=_('Layout'),
        help_text=_('Configurações de layout do dashboard')
    )
    
    publico = models.BooleanField(
        default=False,
        verbose_name=_('Público')
    )
    
    padrao = models.BooleanField(
        default=False,
        verbose_name=_('Dashboard Padrão'),
        help_text=_('Se marcado, será o dashboard padrão do usuário')
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name=_('Usuário')
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
        verbose_name = _('Dashboard Personalizado')
        verbose_name_plural = _('Dashboards Personalizados')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['publico', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.usuario.get_full_name()})"


class FiltroSalvo(models.Model):
    """
    Modelo para salvar filtros personalizados.
    Permite aos usuários salvar combinações de filtros para reutilização.
    """
    
    TIPO_FILTRO_CHOICES = [
        ('processos', _('Processos')),
        ('clientes', _('Clientes')),
        ('documentos', _('Documentos')),
        ('financeiro', _('Financeiro')),
        ('prazos', _('Prazos')),
        ('relatorios', _('Relatórios')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome = models.CharField(
        max_length=200,
        verbose_name=_('Nome do Filtro')
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição')
    )
    
    tipo_filtro = models.CharField(
        max_length=20,
        choices=TIPO_FILTRO_CHOICES,
        verbose_name=_('Tipo de Filtro')
    )
    
    parametros_filtro = models.JSONField(
        default=dict,
        verbose_name=_('Parâmetros do Filtro'),
        help_text=_('Configurações específicas do filtro')
    )
    
    publico = models.BooleanField(
        default=False,
        verbose_name=_('Público')
    )
    
    favorito = models.BooleanField(
        default=False,
        verbose_name=_('Favorito')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='filtros_salvos',
        verbose_name=_('Usuário')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Filtro Salvo')
        verbose_name_plural = _('Filtros Salvos')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['usuario', 'tipo_filtro']),
            models.Index(fields=['publico']),
            models.Index(fields=['favorito']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_filtro_display()})"
