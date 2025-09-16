import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Processo(models.Model):
    """
    Modelo principal para gestão de processos jurídicos.
    Contém todas as informações essenciais de um processo.
    """
    
    TIPO_PROCESSO_CHOICES = [
        ('judicial', _('Judicial')),
        ('administrativo', _('Administrativo')),
        ('consultivo', _('Consultivo')),
        ('extrajudicial', _('Extrajudicial')),
    ]
    
    STATUS_CHOICES = [
        ('ativo', _('Ativo')),
        ('suspenso', _('Suspenso')),
        ('encerrado', _('Encerrado')),
        ('arquivado', _('Arquivado')),
    ]
    
    AREA_DIREITO_CHOICES = [
        ('civil', _('Direito Civil')),
        ('penal', _('Direito Penal')),
        ('trabalhista', _('Direito Trabalhista')),
        ('tributario', _('Direito Tributário')),
        ('empresarial', _('Direito Empresarial')),
        ('familia', _('Direito de Família')),
        ('consumidor', _('Direito do Consumidor')),
        ('previdenciario', _('Direito Previdenciário')),
        ('administrativo', _('Direito Administrativo')),
        ('constitucional', _('Direito Constitucional')),
        ('ambiental', _('Direito Ambiental')),
        ('imobiliario', _('Direito Imobiliário')),
        ('outro', _('Outro')),
    ]
    
    INSTANCIA_CHOICES = [
        ('1_instancia', _('1ª Instância')),
        ('2_instancia', _('2ª Instância')),
        ('superior', _('Tribunal Superior')),
        ('supremo', _('Supremo Tribunal')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do processo')
    )
    
    numero_processo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Número do Processo'),
        help_text=_('Número único do processo no tribunal')
    )
    
    tipo_processo = models.CharField(
        max_length=20,
        choices=TIPO_PROCESSO_CHOICES,
        verbose_name=_('Tipo de Processo')
    )
    
    area_direito = models.CharField(
        max_length=20,
        choices=AREA_DIREITO_CHOICES,
        verbose_name=_('Área do Direito')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name=_('Status')
    )
    
    instancia = models.CharField(
        max_length=15,
        choices=INSTANCIA_CHOICES,
        default='1_instancia',
        verbose_name=_('Instância')
    )
    
    valor_causa = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('Valor da Causa'),
        help_text=_('Valor econômico do processo')
    )
    
    comarca_tribunal = models.CharField(
        max_length=200,
        verbose_name=_('Comarca/Tribunal'),
        help_text=_('Nome da comarca ou tribunal')
    )
    
    vara_orgao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Vara/Órgão'),
        help_text=_('Vara ou órgão específico')
    )
    
    juiz = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Juiz'),
        help_text=_('Nome do juiz responsável')
    )
    
    data_inicio = models.DateField(
        verbose_name=_('Data de Início'),
        help_text=_('Data de distribuição ou início do processo')
    )
    
    data_encerramento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Encerramento')
    )
    
    assunto = models.CharField(
        max_length=500,
        verbose_name=_('Assunto'),
        help_text=_('Resumo do objeto do processo')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações'),
        help_text=_('Informações adicionais sobre o processo')
    )
    
    # Relacionamentos
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='processos',
        verbose_name=_('Cliente')
    )
    
    usuario_responsavel = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='processos_responsavel',
        verbose_name=_('Advogado Responsável')
    )
    
    partes_envolvidas = models.ManyToManyField(
        'clientes.ParteEnvolvida',
        through='ProcessoParteEnvolvida',
        blank=True,
        verbose_name=_('Partes Envolvidas')
    )
    
    # Controle
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
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
        verbose_name = _('Processo')
        verbose_name_plural = _('Processos')
        ordering = ['-data_inicio', 'numero_processo']
        indexes = [
            models.Index(fields=['numero_processo']),
            models.Index(fields=['cliente', '-data_inicio']),
            models.Index(fields=['usuario_responsavel', '-data_inicio']),
            models.Index(fields=['status']),
            models.Index(fields=['area_direito']),
            models.Index(fields=['tipo_processo']),
        ]
    
    def __str__(self):
        return f"{self.numero_processo} - {self.cliente.nome_razao_social}"
    
    @property
    def valor_causa_formatado(self):
        """Retorna o valor da causa formatado em moeda brasileira."""
        if self.valor_causa:
            return f"R$ {self.valor_causa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return 'Não informado'
    
    @property
    def dias_tramitacao(self):
        """Calcula os dias de tramitação do processo."""
        from datetime import date
        data_fim = self.data_encerramento or date.today()
        return (data_fim - self.data_inicio).days
    
    @property
    def ultimo_andamento(self):
        """Retorna o último andamento do processo."""
        return self.andamentos.order_by('-data_andamento').first()
    
    @property
    def proximos_prazos(self):
        """Retorna os próximos prazos não cumpridos."""
        from datetime import date
        return self.prazos.filter(
            cumprido=False,
            data_limite__gte=date.today()
        ).order_by('data_limite')
    
    def pode_ser_editado_por(self, usuario):
        """Verifica se o usuário pode editar o processo."""
        if usuario.is_administrador:
            return True
        if usuario == self.usuario_responsavel:
            return True
        return False


class ProcessoParteEnvolvida(models.Model):
    """
    Modelo intermediário para relacionar processos com partes envolvidas.
    Permite adicionar informações específicas da relação.
    """
    
    POLO_CHOICES = [
        ('ativo', _('Polo Ativo')),
        ('passivo', _('Polo Passivo')),
        ('terceiro', _('Terceiro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        verbose_name=_('Processo')
    )
    
    parte_envolvida = models.ForeignKey(
        'clientes.ParteEnvolvida',
        on_delete=models.CASCADE,
        verbose_name=_('Parte Envolvida')
    )
    
    polo = models.CharField(
        max_length=10,
        choices=POLO_CHOICES,
        verbose_name=_('Polo'),
        help_text=_('Posição da parte no processo')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Processo - Parte Envolvida')
        verbose_name_plural = _('Processos - Partes Envolvidas')
        unique_together = ['processo', 'parte_envolvida']
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.parte_envolvida.nome} ({self.get_polo_display()})"


class Andamento(models.Model):
    """
    Modelo para registrar andamentos processuais.
    Mantém histórico cronológico de todas as movimentações.
    """
    
    TIPO_ANDAMENTO_CHOICES = [
        ('peticao', _('Petição')),
        ('decisao', _('Decisão')),
        ('sentenca', _('Sentença')),
        ('acordao', _('Acórdão')),
        ('intimacao', _('Intimação')),
        ('audiencia', _('Audiência')),
        ('juntada', _('Juntada')),
        ('citacao', _('Citação')),
        ('recurso', _('Recurso')),
        ('despacho', _('Despacho')),
        ('outro', _('Outro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='andamentos',
        verbose_name=_('Processo')
    )
    
    data_andamento = models.DateField(
        verbose_name=_('Data do Andamento')
    )
    
    tipo_andamento = models.CharField(
        max_length=20,
        choices=TIPO_ANDAMENTO_CHOICES,
        verbose_name=_('Tipo de Andamento')
    )
    
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        help_text=_('Detalhes do andamento processual')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações Internas'),
        help_text=_('Anotações internas sobre o andamento')
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário Responsável'),
        help_text=_('Usuário que registrou o andamento')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Andamento')
        verbose_name_plural = _('Andamentos')
        ordering = ['-data_andamento', '-created_at']
        indexes = [
            models.Index(fields=['processo', '-data_andamento']),
            models.Index(fields=['tipo_andamento']),
            models.Index(fields=['data_andamento']),
        ]
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.get_tipo_andamento_display()} ({self.data_andamento.strftime('%d/%m/%Y')})"


class Prazo(models.Model):
    """
    Modelo para controle de prazos processuais.
    Gerencia datas limite e alertas automáticos.
    """
    
    TIPO_PRAZO_CHOICES = [
        ('contestacao', _('Contestação')),
        ('recurso', _('Recurso')),
        ('manifestacao', _('Manifestação')),
        ('audiencia', _('Audiência')),
        ('pericia', _('Perícia')),
        ('cumprimento', _('Cumprimento de Sentença')),
        ('embargos', _('Embargos')),
        ('alegacoes', _('Alegações Finais')),
        ('outro', _('Outro')),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', _('Baixa')),
        ('media', _('Média')),
        ('alta', _('Alta')),
        ('critica', _('Crítica')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='prazos',
        verbose_name=_('Processo')
    )
    
    tipo_prazo = models.CharField(
        max_length=20,
        choices=TIPO_PRAZO_CHOICES,
        verbose_name=_('Tipo de Prazo')
    )
    
    data_limite = models.DateField(
        verbose_name=_('Data Limite'),
        help_text=_('Data final para cumprimento do prazo')
    )
    
    data_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Início'),
        help_text=_('Data de início da contagem do prazo')
    )
    
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        help_text=_('Detalhes sobre o que deve ser feito')
    )
    
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='media',
        verbose_name=_('Prioridade')
    )
    
    cumprido = models.BooleanField(
        default=False,
        verbose_name=_('Cumprido'),
        help_text=_('Indica se o prazo foi cumprido')
    )
    
    data_cumprimento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Cumprimento')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    usuario_responsavel = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário Responsável')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Prazo')
        verbose_name_plural = _('Prazos')
        ordering = ['data_limite', 'prioridade']
        indexes = [
            models.Index(fields=['processo', 'data_limite']),
            models.Index(fields=['data_limite', 'cumprido']),
            models.Index(fields=['usuario_responsavel', 'data_limite']),
            models.Index(fields=['prioridade']),
        ]
    
    def __str__(self):
        status = '✓' if self.cumprido else '⏰'
        return f"{status} {self.processo.numero_processo} - {self.get_tipo_prazo_display()} ({self.data_limite.strftime('%d/%m/%Y')})"
    
    @property
    def dias_restantes(self):
        """Calcula quantos dias restam para o prazo."""
        from datetime import date
        if self.cumprido:
            return 0
        
        hoje = date.today()
        if self.data_limite < hoje:
            return (hoje - self.data_limite).days * -1  # Prazo vencido (negativo)
        return (self.data_limite - hoje).days
    
    @property
    def status_prazo(self):
        """Retorna o status do prazo baseado nos dias restantes."""
        if self.cumprido:
            return 'cumprido'
        
        dias = self.dias_restantes
        if dias < 0:
            return 'vencido'
        elif dias <= 3:
            return 'critico'
        elif dias <= 7:
            return 'atencao'
        else:
            return 'normal'
    
    def marcar_como_cumprido(self, data_cumprimento=None):
        """Marca o prazo como cumprido."""
        from datetime import date
        self.cumprido = True
        self.data_cumprimento = data_cumprimento or date.today()
        self.save()
    
    def clean(self):
        """Validação customizada do modelo."""
        from django.core.exceptions import ValidationError
        from datetime import date
        
        if self.data_inicio and self.data_limite:
            if self.data_inicio > self.data_limite:
                raise ValidationError({
                    'data_limite': _('A data limite deve ser posterior à data de início')
                })
        
        if self.cumprido and not self.data_cumprimento:
            self.data_cumprimento = date.today()
