from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone


class TipoNotificacao(models.TextChoices):
    """Tipos de notificação disponíveis"""
    PRAZO_CRITICO = 'prazo_critico', 'Prazo Crítico'
    PRAZO_VENCIMENTO = 'prazo_vencimento', 'Prazo Vencendo'
    PRAZO_VENCIDO = 'prazo_vencido', 'Prazo Vencido'
    NOVO_ANDAMENTO = 'novo_andamento', 'Novo Andamento'
    DOCUMENTO_UPLOAD = 'documento_upload', 'Documento Enviado'
    SISTEMA = 'sistema', 'Sistema'
    FINANCEIRO = 'financeiro', 'Financeiro'
    CLIENTE = 'cliente', 'Cliente'
    PROCESSO = 'processo', 'Processo'
    SUCESSO = 'sucesso', 'Sucesso'
    ERRO = 'erro', 'Erro'
    AVISO = 'aviso', 'Aviso'
    INFO = 'info', 'Informação'


class PrioridadeNotificacao(models.TextChoices):
    """Níveis de prioridade das notificações"""
    BAIXA = 'baixa', 'Baixa'
    MEDIA = 'media', 'Média'
    ALTA = 'alta', 'Alta'
    CRITICA = 'critica', 'Crítica'


class Notificacao(models.Model):
    """Modelo para notificações do sistema"""
    
    # Relacionamentos
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notificacoes',
        verbose_name='Usuário'
    )
    
    # Campos principais
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    
    mensagem = models.TextField(
        verbose_name='Mensagem'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TipoNotificacao.choices,
        default=TipoNotificacao.INFO,
        verbose_name='Tipo'
    )
    
    prioridade = models.CharField(
        max_length=10,
        choices=PrioridadeNotificacao.choices,
        default=PrioridadeNotificacao.MEDIA,
        verbose_name='Prioridade'
    )
    
    # Status
    lida = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    
    # Metadados opcionais
    url_acao = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Ação',
        help_text='URL para onde o usuário será direcionado ao clicar na notificação'
    )
    
    icone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Ícone',
        help_text='Classe do ícone Bootstrap Icons (ex: bi-bell)'
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
    
    # Timestamps
    criada_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criada em'
    )
    
    lida_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Lida em'
    )
    
    expira_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Expira em',
        help_text='Data de expiração da notificação (opcional)'
    )
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['usuario', '-criada_em']),
            models.Index(fields=['usuario', 'lida']),
            models.Index(fields=['tipo', 'prioridade']),
        ]
    
    def __str__(self):
        return f'{self.titulo} - {self.usuario.get_full_name() or self.usuario.username}'
    
    def marcar_como_lida(self):
        """Marca a notificação como lida"""
        if not self.lida:
            self.lida = True
            self.lida_em = timezone.now()
            self.save(update_fields=['lida', 'lida_em'])
    
    @property
    def conteudo(self):
        texto = self.mensagem or ''
        if self.objeto_id:
            return f"{texto} {self.objeto_id}"
        return texto
    
    def is_expirada(self):
        """Verifica se a notificação está expirada"""
        if self.expira_em:
            return timezone.now() > self.expira_em
        return False
    
    def get_icone_classe(self):
        """Retorna a classe do ícone baseada no tipo"""
        if self.icone:
            return self.icone
        
        icones_tipo = {
            TipoNotificacao.PRAZO_CRITICO: 'bi-exclamation-triangle-fill',
            TipoNotificacao.PRAZO_VENCIDO: 'bi-x-circle-fill',
            TipoNotificacao.NOVO_ANDAMENTO: 'bi-file-text',
            TipoNotificacao.DOCUMENTO_UPLOAD: 'bi-file-earmark-arrow-up',
            TipoNotificacao.SISTEMA: 'bi-gear',
            TipoNotificacao.FINANCEIRO: 'bi-currency-dollar',
            TipoNotificacao.CLIENTE: 'bi-person',
            TipoNotificacao.PROCESSO: 'bi-folder',
            TipoNotificacao.SUCESSO: 'bi-check-circle-fill',
            TipoNotificacao.ERRO: 'bi-x-circle-fill',
            TipoNotificacao.AVISO: 'bi-exclamation-triangle',
            TipoNotificacao.INFO: 'bi-info-circle',
        }
        
        return icones_tipo.get(self.tipo, 'bi-bell')
    
    def get_cor_classe(self):
        """Retorna a classe de cor baseada no tipo e prioridade"""
        if self.prioridade == PrioridadeNotificacao.CRITICA:
            return 'text-danger'
        elif self.prioridade == PrioridadeNotificacao.ALTA:
            return 'text-warning'
        elif self.tipo == TipoNotificacao.SUCESSO:
            return 'text-success'
        elif self.tipo == TipoNotificacao.ERRO:
            return 'text-danger'
        elif self.tipo == TipoNotificacao.AVISO:
            return 'text-warning'
        else:
            return 'text-primary'


class ConfiguracaoNotificacao(models.Model):
    """Configurações de notificação por usuário"""
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='config_notificacoes',
        verbose_name='Usuário'
    )
    
    # Configurações de tipos de notificação
    receber_prazo_critico = models.BooleanField(
        default=True,
        verbose_name='Receber notificações de prazos críticos'
    )
    
    receber_novo_andamento = models.BooleanField(
        default=True,
        verbose_name='Receber notificações de novos andamentos'
    )
    
    receber_documento_upload = models.BooleanField(
        default=True,
        verbose_name='Receber notificações de upload de documentos'
    )
    
    receber_financeiro = models.BooleanField(
        default=True,
        verbose_name='Receber notificações financeiras'
    )
    
    receber_sistema = models.BooleanField(
        default=True,
        verbose_name='Receber notificações do sistema'
    )
    
    # Configurações de entrega
    notificacao_email = models.BooleanField(
        default=False,
        verbose_name='Receber notificações por email'
    )
    
    # Configurações de prazo
    dias_antecedencia_prazo = models.PositiveIntegerField(
        default=3,
        verbose_name='Dias de antecedência para alertas de prazo',
        help_text='Quantos dias antes do vencimento enviar alerta'
    )
    
    # Timestamps
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Notificação'
        verbose_name_plural = 'Configurações de Notificação'
    
    def __str__(self):
        return f'Configurações de {self.usuario.get_full_name() or self.usuario.username}'
