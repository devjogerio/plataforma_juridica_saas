import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json
from datetime import datetime, timedelta

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
        help_text=_(
            'Se marcado, o template estará disponível para todos os usuários')
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

    def criar_agendamento(self, configuracao):
        """Cria uma tarefa agendada para este template."""
        from .tasks import executar_relatorio_agendado

        # Cria configuração de agendamento
        agendamento = AgendamentoRelatorio.objects.create(
            template=self,
            nome=f"Agendamento - {self.nome}",
            configuracao=configuracao,
            usuario_criador=self.usuario_criador
        )

        return agendamento


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
        null=True,
        blank=True,
        verbose_name=_('Data de Conclusão')
    )

    total_registros = models.IntegerField(
        default=0,
        verbose_name=_('Total de Registros')
    )

    arquivo_gerado = models.FileField(
        upload_to='relatorios/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_('Arquivo Gerado')
    )

    tamanho_arquivo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Tamanho do Arquivo')
    )

    mensagem_erro = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Mensagem de Erro')
    )

    duracao_execucao = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_('Duração da Execução')
    )

    class Meta:
        verbose_name = _('Execução de Relatório')
        verbose_name_plural = _('Execuções de Relatórios')
        ordering = ['-data_execucao']
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['usuario']),
            models.Index(fields=['status']),
            models.Index(fields=['data_execucao']),
        ]

    def __str__(self):
        return f"Execução: {self.template.nome} - {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """Calcula a duração da execução ao concluir."""
        if self.status == 'concluido' and self.data_conclusao and not self.duracao_execucao:
            self.duracao_execucao = self.data_conclusao - self.data_execucao
        super().save(*args, **kwargs)

    @property
    def foi_bem_sucedido(self):
        """Verifica se a execução foi bem-sucedida."""
        return self.status == 'concluido' and self.arquivo_gerado

    @property
    def formato_arquivo(self):
        """Retorna o formato do arquivo gerado."""
        if self.arquivo_gerado:
            return self.arquivo_gerado.name.split('.')[-1].upper()
        return None


class AgendamentoRelatorio(models.Model):
    """
    Modelo para agendamento automático de relatórios.
    Permite execuções recorrentes de relatórios com configurações específicas.
    """

    TIPO_AGENDAMENTO_CHOICES = [
        ('diario', _('Diário')),
        ('semanal', _('Semanal')),
        ('mensal', _('Mensal')),
        ('personalizado', _('Personalizado')),
    ]

    STATUS_AGENDAMENTO_CHOICES = [
        ('ativo', _('Ativo')),
        ('pausado', _('Pausado')),
        ('cancelado', _('Cancelado')),
        ('concluido', _('Concluído')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    template = models.ForeignKey(
        TemplateRelatorio,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name=_('Template')
    )

    nome = models.CharField(
        max_length=200,
        verbose_name=_('Nome do Agendamento')
    )

    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição')
    )

    tipo_agendamento = models.CharField(
        max_length=15,
        choices=TIPO_AGENDAMENTO_CHOICES,
        verbose_name=_('Tipo de Agendamento')
    )

    configuracao = models.JSONField(
        default=dict,
        verbose_name=_('Configuração do Agendamento')
    )

    proxima_execucao = models.DateTimeField(
        verbose_name=_('Próxima Execução')
    )

    ultima_execucao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Última Execução')
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_AGENDAMENTO_CHOICES,
        default='ativo',
        verbose_name=_('Status')
    )

    usuario_criador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agendamentos_relatorio',
        verbose_name=_('Usuário Criador')
    )

    destinatarios = models.JSONField(
        default=list,
        verbose_name=_('Destinatários'),
        help_text=_('Lista de emails para envio automático')
    )

    manter_historico = models.BooleanField(
        default=True,
        verbose_name=_('Manter Histórico'),
        help_text=_('Manter histórico das execuções agendadas')
    )

    dias_manter_historico = models.IntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name=_('Dias para Manter Histórico')
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
        verbose_name = _('Agendamento de Relatório')
        verbose_name_plural = _('Agendamentos de Relatórios')
        ordering = ['proxima_execucao']
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['usuario_criador']),
            models.Index(fields=['status']),
            models.Index(fields=['proxima_execucao']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_tipo_agendamento_display()}"

    def calcular_proxima_execucao(self):
        """Calcula a próxima execução baseada na configuração."""
        from .utils import calcular_proxima_execucao_agendamento
        return calcular_proxima_execucao_agendamento(self)

    def executar_agora(self):
        """Executa o relatório imediatamente."""
        from .tasks import executar_relatorio_agendado
        return executar_relatorio_agendado.delay(self.id)

    def pausar(self):
        """Pausa o agendamento."""
        self.status = 'pausado'
        self.save()

    def retomar(self):
        """Retoma o agendamento pausado."""
        self.status = 'ativo'
        self.proxima_execucao = self.calcular_proxima_execucao()
        self.save()

    def cancelar(self):
        """Cancela o agendamento."""
        self.status = 'cancelado'
        self.save()


class FiltroAvancado(models.Model):
    """
    Modelo para filtros avançados e reutilizáveis.
    Permite criar filtros complexos que podem ser salvos e reutilizados.
    """

    TIPO_FILTRO_CHOICES = [
        ('processo', _('Processo')),
        ('cliente', _('Cliente')),
        ('financeiro', _('Financeiro')),
        ('documento', _('Documento')),
        ('usuario', _('Usuário')),
        ('data', _('Data')),
        ('status', _('Status')),
        ('personalizado', _('Personalizado')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    nome = models.CharField(
        max_length=100,
        verbose_name=_('Nome do Filtro')
    )

    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição')
    )

    tipo_filtro = models.CharField(
        max_length=15,
        choices=TIPO_FILTRO_CHOICES,
        verbose_name=_('Tipo de Filtro')
    )

    condicoes = models.JSONField(
        default=list,
        verbose_name=_('Condições do Filtro'),
        help_text=_('Lista de condições para aplicação do filtro')
    )

    publico = models.BooleanField(
        default=False,
        verbose_name=_('Público'),
        help_text=_('Disponível para todos os usuários')
    )

    usuario_criador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='filtros_avancados',
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
        verbose_name = _('Filtro Avançado')
        verbose_name_plural = _('Filtros Avançados')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['tipo_filtro']),
            models.Index(fields=['usuario_criador']),
            models.Index(fields=['publico']),
        ]

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_filtro_display()})"

    def aplicar_filtro(self, queryset):
        """Aplica o filtro a um queryset."""
        from .utils import aplicar_filtros_avancados
        return aplicar_filtros_avancados(queryset, self.condicoes)

    @property
    def total_uso(self):
        """Retorna o número de vezes que o filtro foi usado."""
        return TemplateRelatorio.objects.filter(
            filtros_padrao__contains={'filtro_id': str(self.id)}
        ).count()


class ConfiguracaoExportacao(models.Model):
    """
    Modelo para configurações avançadas de exportação.
    Permite personalizar formatação, layout e opções de exportação.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    nome = models.CharField(
        max_length=100,
        verbose_name=_('Nome da Configuração')
    )

    formato = models.CharField(
        max_length=10,
        choices=TemplateRelatorio.FORMATO_SAIDA_CHOICES,
        verbose_name=_('Formato de Saída')
    )

    configuracoes = models.JSONField(
        default=dict,
        verbose_name=_('Configurações de Exportação')
    )

    # Configurações específicas para PDF
    orientacao_pagina = models.CharField(
        max_length=10,
        choices=[('portrait', _('Retrato')), ('landscape', _('Paisagem'))],
        default='portrait',
        verbose_name=_('Orientação da Página')
    )

    incluir_cabecalho = models.BooleanField(
        default=True,
        verbose_name=_('Incluir Cabeçalho')
    )

    incluir_rodape = models.BooleanField(
        default=True,
        verbose_name=_('Incluir Rodapé')
    )

    # Configurações específicas para Excel
    auto_filter = models.BooleanField(
        default=True,
        verbose_name=_('Auto Filtro')
    )

    freeze_panes = models.BooleanField(
        default=True,
        verbose_name=_('Congelar Painéis')
    )

    usuario_criador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='configuracoes_exportacao',
        verbose_name=_('Usuário Criador')
    )

    publico = models.BooleanField(
        default=False,
        verbose_name=_('Público')
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
        verbose_name = _('Configuração de Exportação')
        verbose_name_plural = _('Configurações de Exportação')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['formato']),
            models.Index(fields=['usuario_criador']),
        ]

    def __str__(self):
        return f"{self.nome} ({self.get_formato_display()})"

    def aplicar_configuracao(self, exportador):
        """Aplica a configuração a um objeto exportador."""
        from .exportadores import aplicar_configuracao_exportacao
        return aplicar_configuracao_exportacao(exportador, self.configuracoes)


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
