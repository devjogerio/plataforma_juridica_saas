import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


def upload_honorario_documento(instance, filename):
    """
    Função para definir o caminho de upload dos documentos de honorários
    """
    return f'honorarios/{instance.honorario.id}/documentos/{filename}'


class Honorario(models.Model):
    """
    Modelo para controle de honorários advocatícios.
    Gerencia diferentes tipos de cobrança e parcelas.
    """
    
    TIPO_COBRANCA_CHOICES = [
        ('fixo', _('Valor Fixo')),
        ('por_hora', _('Por Hora')),
        ('por_exito', _('Por Êxito')),
        ('misto', _('Misto (Fixo + Êxito)')),
        ('pro_bono', _('Pro Bono')),
    ]
    
    STATUS_PAGAMENTO_CHOICES = [
        ('pendente', _('Pendente')),
        ('parcial', _('Parcialmente Pago')),
        ('pago', _('Pago')),
        ('cancelado', _('Cancelado')),
        ('em_cobranca', _('Em Cobrança')),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', _('Dinheiro')),
        ('transferencia', _('Transferência Bancária')),
        ('pix', _('PIX')),
        ('cartao_credito', _('Cartão de Crédito')),
        ('cartao_debito', _('Cartão de Débito')),
        ('boleto', _('Boleto Bancário')),
        ('cheque', _('Cheque')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do honorário')
    )
    
    processo = models.ForeignKey(
        'processos.Processo',
        on_delete=models.PROTECT,
        related_name='honorarios',
        verbose_name=_('Processo')
    )
    
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='honorarios',
        verbose_name=_('Cliente')
    )
    
    tipo_cobranca = models.CharField(
        max_length=15,
        choices=TIPO_COBRANCA_CHOICES,
        verbose_name=_('Tipo de Cobrança')
    )
    
    valor_fixo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        verbose_name=_('Valor Fixo'),
        help_text=_('Valor fixo do honorário')
    )
    
    valor_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        verbose_name=_('Valor por Hora'),
        help_text=_('Valor cobrado por hora trabalhada')
    )
    
    horas_trabalhadas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        verbose_name=_('Horas Trabalhadas'),
        help_text=_('Total de horas trabalhadas no processo')
    )
    
    percentual_exito = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        blank=True,
        null=True,
        verbose_name=_('Percentual de Êxito (%)'),
        help_text=_('Percentual sobre o valor obtido em caso de êxito')
    )
    
    valor_exito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        verbose_name=_('Valor do Êxito'),
        help_text=_('Valor obtido no processo para cálculo do êxito')
    )
    
    valor_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor Total'),
        help_text=_('Valor total do honorário')
    )
    
    status_pagamento = models.CharField(
        max_length=15,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente',
        verbose_name=_('Status do Pagamento')
    )
    
    data_vencimento = models.DateField(
        verbose_name=_('Data de Vencimento')
    )
    
    data_pagamento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Pagamento')
    )
    
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Forma de Pagamento')
    )
    
    numero_parcelas = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Número de Parcelas'),
        help_text=_('Quantidade de parcelas para pagamento')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações'),
        help_text=_('Informações adicionais sobre o honorário')
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
        verbose_name = _('Honorário')
        verbose_name_plural = _('Honorários')
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['processo']),
            models.Index(fields=['cliente']),
            models.Index(fields=['status_pagamento']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['tipo_cobranca']),
        ]
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.get_tipo_cobranca_display()} - R$ {self.valor_total}"
    
    def save(self, *args, **kwargs):
        """Calcula o valor total automaticamente baseado no tipo de cobrança."""
        self.valor_total = self.calcular_valor_total()
        super().save(*args, **kwargs)
    
    def calcular_valor_total(self):
        """Calcula o valor total do honorário baseado no tipo de cobrança."""
        total = Decimal('0.00')
        
        if self.tipo_cobranca == 'fixo' and self.valor_fixo:
            total = self.valor_fixo
        
        elif self.tipo_cobranca == 'por_hora' and self.valor_hora and self.horas_trabalhadas:
            total = self.valor_hora * self.horas_trabalhadas
        
        elif self.tipo_cobranca == 'por_exito' and self.percentual_exito and self.valor_exito:
            total = (self.valor_exito * self.percentual_exito) / Decimal('100.00')
        
        elif self.tipo_cobranca == 'misto':
            # Soma valor fixo + percentual de êxito
            if self.valor_fixo:
                total += self.valor_fixo
            if self.percentual_exito and self.valor_exito:
                total += (self.valor_exito * self.percentual_exito) / Decimal('100.00')
        
        elif self.tipo_cobranca == 'pro_bono':
            total = Decimal('0.00')
        
        return total
    
    @property
    def valor_total_formatado(self):
        """Retorna o valor total formatado em moeda brasileira."""
        return f"R$ {self.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_pago(self):
        """Calcula o valor já pago através das parcelas."""
        return sum(parcela.valor_pago for parcela in self.parcelas.all())
    
    @property
    def valor_pendente(self):
        """Calcula o valor ainda pendente de pagamento."""
        return self.valor_total - self.valor_pago
    
    @property
    def percentual_pago(self):
        """Calcula o percentual já pago."""
        if self.valor_total > 0:
            return (self.valor_pago / self.valor_total) * 100
        return 0
    
    @property
    def is_vencido(self):
        """Verifica se o honorário está vencido."""
        from datetime import date
        return self.data_vencimento < date.today() and self.status_pagamento != 'pago'
    
    def gerar_parcelas(self):
        """Gera as parcelas do honorário automaticamente."""
        # Remove parcelas existentes
        self.parcelas.all().delete()
        
        if self.numero_parcelas <= 0:
            return
        
        valor_parcela = self.valor_total / self.numero_parcelas
        
        from dateutil.relativedelta import relativedelta
        
        for i in range(self.numero_parcelas):
            data_vencimento = self.data_vencimento + relativedelta(months=i)
            
            ParcelaHonorario.objects.create(
                honorario=self,
                numero_parcela=i + 1,
                valor_parcela=valor_parcela,
                data_vencimento=data_vencimento
            )


class ParcelaHonorario(models.Model):
    """
    Modelo para controle de parcelas de honorários.
    Permite parcelamento dos pagamentos.
    """
    
    STATUS_CHOICES = [
        ('pendente', _('Pendente')),
        ('pago', _('Pago')),
        ('cancelado', _('Cancelado')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    honorario = models.ForeignKey(
        Honorario,
        on_delete=models.CASCADE,
        related_name='parcelas',
        verbose_name=_('Honorário')
    )
    
    numero_parcela = models.PositiveIntegerField(
        verbose_name=_('Número da Parcela')
    )
    
    valor_parcela = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor da Parcela')
    )
    
    valor_pago = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        verbose_name=_('Valor Pago')
    )
    
    data_vencimento = models.DateField(
        verbose_name=_('Data de Vencimento')
    )
    
    data_pagamento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Pagamento')
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name=_('Status')
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
        verbose_name = _('Parcela de Honorário')
        verbose_name_plural = _('Parcelas de Honorários')
        ordering = ['honorario', 'numero_parcela']
        unique_together = ['honorario', 'numero_parcela']
    
    def __str__(self):
        return f"{self.honorario.processo.numero_processo} - Parcela {self.numero_parcela}/{self.honorario.numero_parcelas}"
    
    @property
    def is_vencida(self):
        """Verifica se a parcela está vencida."""
        from datetime import date
        return self.data_vencimento < date.today() and self.status != 'pago'
    
    def marcar_como_paga(self, valor_pago=None, data_pagamento=None):
        """Marca a parcela como paga."""
        from datetime import date
        
        self.valor_pago = valor_pago or self.valor_parcela
        self.data_pagamento = data_pagamento or date.today()
        self.status = 'pago'
        self.save()
        
        # Atualiza o status do honorário pai
        self.honorario.atualizar_status_pagamento()


class Despesa(models.Model):
    """
    Modelo para controle de despesas processuais.
    Registra custas, taxas e outras despesas relacionadas aos processos.
    """
    
    TIPO_DESPESA_CHOICES = [
        ('custas_judiciais', _('Custas Judiciais')),
        ('taxa_judiciaria', _('Taxa Judiciária')),
        ('pericia', _('Perícia')),
        ('diligencia', _('Diligência')),
        ('viagem', _('Viagem')),
        ('correios', _('Correios')),
        ('cartorio', _('Cartório')),
        ('publicacao', _('Publicação')),
        ('xerox', _('Xerox/Impressão')),
        ('telefone', _('Telefone')),
        ('internet', _('Internet')),
        ('material_escritorio', _('Material de Escritório')),
        ('outra', _('Outra')),
    ]
    
    STATUS_REEMBOLSO_CHOICES = [
        ('nao_reembolsavel', _('Não Reembolsável')),
        ('pendente', _('Pendente de Reembolso')),
        ('reembolsado', _('Reembolsado')),
        ('cancelado', _('Cancelado')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único da despesa')
    )
    
    processo = models.ForeignKey(
        'processos.Processo',
        on_delete=models.PROTECT,
        related_name='despesas',
        verbose_name=_('Processo')
    )
    
    tipo_despesa = models.CharField(
        max_length=25,
        choices=TIPO_DESPESA_CHOICES,
        verbose_name=_('Tipo de Despesa')
    )
    
    descricao = models.CharField(
        max_length=500,
        verbose_name=_('Descrição'),
        help_text=_('Descrição detalhada da despesa')
    )
    
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Valor'),
        help_text=_('Valor da despesa')
    )
    
    data_despesa = models.DateField(
        verbose_name=_('Data da Despesa'),
        help_text=_('Data em que a despesa foi realizada')
    )
    
    status_reembolso = models.CharField(
        max_length=20,
        choices=STATUS_REEMBOLSO_CHOICES,
        default='pendente',
        verbose_name=_('Status de Reembolso')
    )
    
    data_reembolso = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Reembolso')
    )
    
    fornecedor = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Fornecedor'),
        help_text=_('Nome do fornecedor ou prestador de serviço')
    )
    
    numero_documento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Número do Documento'),
        help_text=_('Número da nota fiscal, recibo, etc.')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    usuario_lancamento = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário que Lançou')
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
        verbose_name = _('Despesa')
        verbose_name_plural = _('Despesas')
        ordering = ['-data_despesa']
        indexes = [
            models.Index(fields=['processo', '-data_despesa']),
            models.Index(fields=['tipo_despesa']),
            models.Index(fields=['status_reembolso']),
            models.Index(fields=['data_despesa']),
        ]
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.get_tipo_despesa_display()} - R$ {self.valor}"
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado em moeda brasileira."""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def marcar_como_reembolsada(self, data_reembolso=None):
        """Marca a despesa como reembolsada."""
        from datetime import date
        
        self.status_reembolso = 'reembolsado'
        self.data_reembolso = data_reembolso or date.today()
        self.save()


class ContaBancaria(models.Model):
    """
    Modelo para controle de contas bancárias do escritório.
    Usado para controle financeiro e conciliação.
    """
    
    TIPO_CONTA_CHOICES = [
        ('corrente', _('Conta Corrente')),
        ('poupanca', _('Conta Poupança')),
        ('investimento', _('Conta Investimento')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome_conta = models.CharField(
        max_length=100,
        verbose_name=_('Nome da Conta'),
        help_text=_('Nome identificador da conta')
    )
    
    banco = models.CharField(
        max_length=100,
        verbose_name=_('Banco')
    )
    
    agencia = models.CharField(
        max_length=20,
        verbose_name=_('Agência')
    )
    
    numero_conta = models.CharField(
        max_length=30,
        verbose_name=_('Número da Conta')
    )
    
    tipo_conta = models.CharField(
        max_length=15,
        choices=TIPO_CONTA_CHOICES,
        verbose_name=_('Tipo de Conta')
    )
    
    saldo_inicial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Saldo Inicial')
    )
    
    ativa = models.BooleanField(
        default=True,
        verbose_name=_('Ativa')
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
        verbose_name = _('Conta Bancária')
        verbose_name_plural = _('Contas Bancárias')
        ordering = ['nome_conta']
    
    def __str__(self):
        return f"{self.nome_conta} - {self.banco}"
    
    @property
    def saldo_atual(self):
        """Calcula o saldo atual da conta."""
        # Implementar cálculo baseado em movimentações
        return self.saldo_inicial


class DocumentoHonorario(models.Model):
    """
    Modelo para armazenar documentos anexados aos honorários
    """
    
    TIPO_DOCUMENTO_CHOICES = [
        ('contrato', _('Contrato de Honorários')),
        ('nota_fiscal', _('Nota Fiscal')),
        ('recibo', _('Recibo')),
        ('comprovante_pagamento', _('Comprovante de Pagamento')),
        ('acordo', _('Acordo/Termo')),
        ('correspondencia', _('Correspondência')),
        ('outro', _('Outro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do documento')
    )
    
    honorario = models.ForeignKey(
        Honorario,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name=_('Honorário')
    )
    
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name=_('Nome do Arquivo'),
        help_text=_('Nome original do arquivo')
    )
    
    arquivo = models.FileField(
        upload_to=upload_honorario_documento,
        verbose_name=_('Arquivo'),
        help_text=_('Arquivo do documento (PDF, DOC, DOCX, JPG, PNG)')
    )
    
    tipo_documento = models.CharField(
        max_length=25,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name=_('Tipo de Documento')
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição do conteúdo do documento')
    )
    
    tamanho_arquivo = models.PositiveIntegerField(
        verbose_name=_('Tamanho do Arquivo (bytes)'),
        help_text=_('Tamanho do arquivo em bytes')
    )
    
    usuario_upload = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário que fez o Upload')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Upload')
    )
    
    class Meta:
        verbose_name = _('Documento de Honorário')
        verbose_name_plural = _('Documentos de Honorários')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['honorario', '-created_at']),
            models.Index(fields=['tipo_documento']),
        ]
    
    def __str__(self):
        return f"{self.nome_arquivo} - {self.honorario}"
    
    def save(self, *args, **kwargs):
        if self.arquivo:
            self.tamanho_arquivo = self.arquivo.size
            if not self.nome_arquivo:
                self.nome_arquivo = os.path.basename(self.arquivo.name)
        super().save(*args, **kwargs)
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado em KB/MB"""
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} bytes"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"
    
    @property
    def extensao_arquivo(self):
        """Retorna a extensão do arquivo"""
        return os.path.splitext(self.nome_arquivo)[1].lower()
    
    @property
    def is_imagem(self):
        """Verifica se o arquivo é uma imagem"""
        extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        return self.extensao_arquivo in extensoes_imagem
    
    @property
    def is_pdf(self):
        """Verifica se o arquivo é um PDF"""
        return self.extensao_arquivo == '.pdf'
