from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid


User = get_user_model()


class TipoAlerta(models.TextChoices):
    """Tipos de alerta disponíveis"""
    PRAZO_PROCESSO = 'prazo_processo', 'Prazo Processual'
    AUDIENCIA = 'audiencia', 'Audiência'
    REUNIAO = 'reuniao', 'Reunião'
    VENCIMENTO_DOCUMENTO = 'vencimento_documento', 'Vencimento de Documento'
    PAGAMENTO = 'pagamento', 'Pagamento'
    TAREFA = 'tarefa', 'Tarefa'
    EVENTO = 'evento', 'Evento'
    LEMBRETE = 'lembrete', 'Lembrete'
    ANIVERSARIO = 'aniversario', 'Aniversário'
    OUTRO = 'outro', 'Outro'


class PrioridadeAlerta(models.TextChoices):
    """Níveis de prioridade dos alertas"""
    BAIXA = 'baixa', 'Baixa'
    MEDIA = 'media', 'Média'
    ALTA = 'alta', 'Alta'
    CRITICA = 'critica', 'Crítica'


class StatusAlerta(models.TextChoices):
    """Status do alerta"""
    ATIVO = 'ativo', 'Ativo'
    CONCLUIDO = 'concluido', 'Concluído'
    CANCELADO = 'cancelado', 'Cancelado'
    ADIADO = 'adiado', 'Adiado'


class Alerta(models.Model):
    """Modelo principal para alertas e lembretes"""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Relacionamentos
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name='Usuário'
    )
    
    # Campos principais
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TipoAlerta.choices,
        default=TipoAlerta.LEMBRETE,
        verbose_name='Tipo'
    )
    
    prioridade = models.CharField(
        max_length=10,
        choices=PrioridadeAlerta.choices,
        default=PrioridadeAlerta.MEDIA,
        verbose_name='Prioridade'
    )
    
    status = models.CharField(
        max_length=10,
        choices=StatusAlerta.choices,
        default=StatusAlerta.ATIVO,
        verbose_name='Status'
    )
    
    # Datas e horários
    data_alerta = models.DateTimeField(
        verbose_name='Data e Hora do Alerta',
        help_text='Quando o alerta deve ser disparado'
    )
    
    data_vencimento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data de Vencimento',
        help_text='Data limite para a ação (opcional)'
    )
    
    # Configurações de repetição
    recorrente = models.BooleanField(
        default=False,
        verbose_name='Recorrente',
        help_text='Se o alerta deve se repetir'
    )
    
    frequencia_recorrencia = models.CharField(
        max_length=20,
        choices=[
            ('diario', 'Diário'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
            ('anual', 'Anual'),
        ],
        blank=True,
        null=True,
        verbose_name='Frequência de Recorrência'
    )
    
    # Configurações de notificação
    notificar_email = models.BooleanField(
        default=False,
        verbose_name='Notificar por Email'
    )
    
    antecedencia_minutos = models.PositiveIntegerField(
        default=60,
        verbose_name='Antecedência (minutos)',
        help_text='Quantos minutos antes disparar o alerta'
    )
    
    # Referências opcionais para objetos relacionados
    objeto_tipo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tipo do Objeto',
        help_text='Tipo do objeto relacionado (ex: processo, cliente)'
    )
    
    objeto_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID do Objeto',
        help_text='ID do objeto relacionado'
    )
    
    # URL de ação
    url_acao = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Ação',
        help_text='URL para onde o usuário será direcionado'
    )
    
    # Controle de notificações
    notificado_antecedencia = models.BooleanField(
        default=False,
        verbose_name='Notificado Antecedência',
        help_text='Se já foi enviada notificação de antecedência'
    )
    
    notificado_vencimento = models.BooleanField(
        default=False,
        verbose_name='Notificado Vencimento',
        help_text='Se já foi enviada notificação de vencimento'
    )
    
    # Timestamps
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    concluido_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Concluído em'
    )
    
    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['data_alerta', '-prioridade']
        indexes = [
            models.Index(fields=['usuario', 'status']),
            models.Index(fields=['data_alerta', 'status']),
            models.Index(fields=['tipo', 'prioridade']),
            models.Index(fields=['objeto_tipo', 'objeto_id']),
        ]
    
    def __str__(self):
        return f'{self.titulo} - {self.get_prioridade_display()}'
    
    def clean(self):
        """Validações customizadas"""
        if self.data_vencimento and self.data_alerta > self.data_vencimento:
            raise ValidationError('A data do alerta não pode ser posterior à data de vencimento.')
        
        if self.recorrente and not self.frequencia_recorrencia:
            raise ValidationError('Frequência de recorrência é obrigatória para alertas recorrentes.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def marcar_como_concluido(self):
        """Marca o alerta como concluído"""
        self.status = StatusAlerta.CONCLUIDO
        self.concluido_em = timezone.now()
        self.save(update_fields=['status', 'concluido_em'])
    
    def adiar(self, nova_data):
        """Adia o alerta para uma nova data"""
        self.data_alerta = nova_data
        self.status = StatusAlerta.ADIADO
        self.save(update_fields=['data_alerta', 'status'])
    
    def cancelar(self):
        """Cancela o alerta"""
        self.status = StatusAlerta.CANCELADO
        self.save(update_fields=['status'])
    
    @property
    def esta_vencido(self):
        """Verifica se o alerta está vencido"""
        if self.data_vencimento:
            return timezone.now() > self.data_vencimento
        return False
    
    @property
    def tempo_restante(self):
        """Retorna o tempo restante até o alerta"""
        if self.data_alerta > timezone.now():
            return self.data_alerta - timezone.now()
        return None
    
    @property
    def deve_disparar(self):
        """Verifica se o alerta deve ser disparado agora"""
        if self.status != StatusAlerta.ATIVO:
            return False
        
        agora = timezone.now()
        data_disparo = self.data_alerta - timezone.timedelta(minutes=self.antecedencia_minutos)
        
        return agora >= data_disparo
    
    def get_icone_classe(self):
        """Retorna a classe do ícone baseada no tipo"""
        icones_tipo = {
            TipoAlerta.PRAZO_PROCESSO: 'bi-calendar-check',
            TipoAlerta.AUDIENCIA: 'bi-people',
            TipoAlerta.REUNIAO: 'bi-calendar-event',
            TipoAlerta.VENCIMENTO_DOCUMENTO: 'bi-file-earmark-text',
            TipoAlerta.PAGAMENTO: 'bi-currency-dollar',
            TipoAlerta.TAREFA: 'bi-check-square',
            TipoAlerta.EVENTO: 'bi-calendar',
            TipoAlerta.LEMBRETE: 'bi-bell',
            TipoAlerta.ANIVERSARIO: 'bi-gift',
            TipoAlerta.OUTRO: 'bi-info-circle',
        }
        
        return icones_tipo.get(self.tipo, 'bi-bell')
    
    def get_cor_prioridade(self):
        """Retorna a cor baseada na prioridade"""
        cores_prioridade = {
            PrioridadeAlerta.BAIXA: 'success',
            PrioridadeAlerta.MEDIA: 'warning',
            PrioridadeAlerta.ALTA: 'danger',
            PrioridadeAlerta.CRITICA: 'dark',
        }
        
        return cores_prioridade.get(self.prioridade, 'secondary')


class HistoricoAlerta(models.Model):
    """Histórico de ações realizadas nos alertas"""
    
    ACAO_CHOICES = [
        ('criado', 'Criado'),
        ('editado', 'Editado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('adiado', 'Adiado'),
        ('disparado', 'Disparado'),
    ]
    
    alerta = models.ForeignKey(
        Alerta,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name='Alerta'
    )
    
    acao = models.CharField(
        max_length=20,
        choices=ACAO_CHOICES,
        verbose_name='Ação'
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    
    data_acao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Ação'
    )
    
    class Meta:
        verbose_name = 'Histórico de Alerta'
        verbose_name_plural = 'Históricos de Alertas'
        ordering = ['-data_acao']
    
    def __str__(self):
        return f'{self.alerta.titulo} - {self.get_acao_display()}'


class ConfiguracaoAlerta(models.Model):
    """Configurações de alertas por usuário"""
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='config_alertas',
        verbose_name='Usuário'
    )
    
    # Configurações gerais
    alertas_ativos = models.BooleanField(
        default=True,
        verbose_name='Alertas Ativos',
        help_text='Receber alertas do sistema'
    )
    
    # Configurações por tipo
    alertas_prazos = models.BooleanField(
        default=True,
        verbose_name='Alertas de Prazos'
    )
    
    alertas_audiencias = models.BooleanField(
        default=True,
        verbose_name='Alertas de Audiências'
    )
    
    alertas_reunioes = models.BooleanField(
        default=True,
        verbose_name='Alertas de Reuniões'
    )
    
    alertas_pagamentos = models.BooleanField(
        default=True,
        verbose_name='Alertas de Pagamentos'
    )
    
    alertas_tarefas = models.BooleanField(
        default=True,
        verbose_name='Alertas de Tarefas'
    )
    
    # Configurações de notificação
    notificacao_email = models.BooleanField(
        default=False,
        verbose_name='Notificações por Email'
    )
    
    notificacao_push = models.BooleanField(
        default=True,
        verbose_name='Notificações Push'
    )
    
    # Configurações de antecedência padrão
    antecedencia_padrao = models.PositiveIntegerField(
        default=60,
        verbose_name='Antecedência Padrão (minutos)',
        help_text='Antecedência padrão para novos alertas'
    )
    
    # Horários de funcionamento
    horario_inicio = models.TimeField(
        default='08:00',
        verbose_name='Horário de Início',
        help_text='Não enviar alertas antes deste horário'
    )
    
    horario_fim = models.TimeField(
        default='18:00',
        verbose_name='Horário de Fim',
        help_text='Não enviar alertas após este horário'
    )
    
    # Dias da semana
    alertas_fins_semana = models.BooleanField(
        default=False,
        verbose_name='Alertas nos Fins de Semana'
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Alerta'
        verbose_name_plural = 'Configurações de Alertas'
    
    def __str__(self):
        return f'Configurações de {self.usuario.get_full_name() or self.usuario.username}'