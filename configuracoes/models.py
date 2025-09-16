from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.utils import timezone


class TipoProcesso(models.Model):
    """Tipos de processo configuráveis"""
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Tipo',
        validators=[MinLengthValidator(2)]
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do tipo de processo'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único para identificação (ex: CIV, TRAB, CRIM)'
    )
    
    cor = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name='Cor',
        help_text='Cor em hexadecimal para identificação visual'
    )
    
    icone = models.CharField(
        max_length=50,
        default='bi-folder',
        verbose_name='Ícone',
        help_text='Classe do ícone Bootstrap Icons'
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tipos_processo_criados',
        verbose_name='Criado por'
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Tipo de Processo'
        verbose_name_plural = 'Tipos de Processo'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['ativo', 'ordem']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f'{self.codigo} - {self.nome}'
    
    def save(self, *args, **kwargs):
        self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)


class AreaDireito(models.Model):
    """Áreas do direito configuráveis"""
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome da Área',
        validators=[MinLengthValidator(2)]
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único para identificação'
    )
    
    cor = models.CharField(
        max_length=7,
        default='#28a745',
        verbose_name='Cor',
        help_text='Cor em hexadecimal para identificação visual'
    )
    
    icone = models.CharField(
        max_length=50,
        default='bi-scales',
        verbose_name='Ícone',
        help_text='Classe do ícone Bootstrap Icons'
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='areas_direito_criadas',
        verbose_name='Criado por'
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Área do Direito'
        verbose_name_plural = 'Áreas do Direito'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['ativo', 'ordem']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f'{self.codigo} - {self.nome}'
    
    def save(self, *args, **kwargs):
        self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)


class StatusProcesso(models.Model):
    """Status de processo personalizáveis"""
    
    nome = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nome do Status',
        validators=[MinLengthValidator(2)]
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único para identificação'
    )
    
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Cor',
        help_text='Cor em hexadecimal para identificação visual'
    )
    
    icone = models.CharField(
        max_length=50,
        default='bi-circle',
        verbose_name='Ícone',
        help_text='Classe do ícone Bootstrap Icons'
    )
    
    # Configurações de comportamento
    is_inicial = models.BooleanField(
        default=False,
        verbose_name='Status Inicial',
        help_text='Define se este é o status padrão para novos processos'
    )
    
    is_final = models.BooleanField(
        default=False,
        verbose_name='Status Final',
        help_text='Define se este status indica processo encerrado'
    )
    
    permite_edicao = models.BooleanField(
        default=True,
        verbose_name='Permite Edição',
        help_text='Define se processos com este status podem ser editados'
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_processo_criados',
        verbose_name='Criado por'
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Status de Processo'
        verbose_name_plural = 'Status de Processo'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['ativo', 'ordem']),
            models.Index(fields=['codigo']),
            models.Index(fields=['is_inicial']),
            models.Index(fields=['is_final']),
        ]
    
    def __str__(self):
        return f'{self.codigo} - {self.nome}'
    
    def save(self, *args, **kwargs):
        self.codigo = self.codigo.upper()
        
        # Garantir que apenas um status seja inicial
        if self.is_inicial:
            StatusProcesso.objects.filter(is_inicial=True).exclude(pk=self.pk).update(is_inicial=False)
        
        super().save(*args, **kwargs)


class ModeloDocumento(models.Model):
    """Modelos de documentos configuráveis"""
    
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Modelo',
        validators=[MinLengthValidator(2)]
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    categoria = models.CharField(
        max_length=50,
        verbose_name='Categoria',
        help_text='Categoria do documento (ex: Petição, Contrato, Parecer)'
    )
    
    conteudo = models.TextField(
        verbose_name='Conteúdo do Modelo',
        help_text='Conteúdo do documento com variáveis substituíveis'
    )
    
    variaveis = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Variáveis Disponíveis',
        help_text='Dicionário com as variáveis disponíveis e suas descrições'
    )
    
    # Configurações
    tipo_arquivo = models.CharField(
        max_length=10,
        choices=[
            ('docx', 'Word Document (.docx)'),
            ('pdf', 'PDF Document (.pdf)'),
            ('txt', 'Text File (.txt)'),
            ('html', 'HTML Document (.html)'),
        ],
        default='docx',
        verbose_name='Tipo de Arquivo'
    )
    
    publico = models.BooleanField(
        default=False,
        verbose_name='Público',
        help_text='Define se o modelo está disponível para todos os usuários'
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    # Relacionamentos
    areas_direito = models.ManyToManyField(
        AreaDireito,
        blank=True,
        verbose_name='Áreas do Direito',
        help_text='Áreas do direito relacionadas a este modelo'
    )
    
    tipos_processo = models.ManyToManyField(
        TipoProcesso,
        blank=True,
        verbose_name='Tipos de Processo',
        help_text='Tipos de processo relacionados a este modelo'
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='modelos_documento_criados',
        verbose_name='Criado por'
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # Estatísticas
    vezes_usado = models.PositiveIntegerField(
        default=0,
        verbose_name='Vezes Usado'
    )
    
    ultimo_uso = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Uso'
    )
    
    class Meta:
        verbose_name = 'Modelo de Documento'
        verbose_name_plural = 'Modelos de Documento'
        ordering = ['-ultimo_uso', '-criado_em']
        indexes = [
            models.Index(fields=['ativo', 'publico']),
            models.Index(fields=['categoria']),
            models.Index(fields=['criado_por']),
            models.Index(fields=['-vezes_usado']),
        ]
    
    def __str__(self):
        return f'{self.categoria} - {self.nome}'
    
    def incrementar_uso(self):
        """Incrementa contador de uso"""
        self.vezes_usado += 1
        self.ultimo_uso = timezone.now()
        self.save(update_fields=['vezes_usado', 'ultimo_uso'])


class ConfiguracaoSistema(models.Model):
    """Configurações gerais do sistema"""
    
    chave = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Chave',
        help_text='Identificador único da configuração'
    )
    
    valor = models.TextField(
        verbose_name='Valor',
        help_text='Valor da configuração'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('string', 'Texto'),
            ('integer', 'Número Inteiro'),
            ('float', 'Número Decimal'),
            ('boolean', 'Verdadeiro/Falso'),
            ('json', 'JSON'),
            ('date', 'Data'),
            ('datetime', 'Data e Hora'),
        ],
        default='string',
        verbose_name='Tipo de Dados'
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição da configuração'
    )
    
    categoria = models.CharField(
        max_length=50,
        default='geral',
        verbose_name='Categoria',
        help_text='Categoria da configuração para organização'
    )
    
    editavel = models.BooleanField(
        default=True,
        verbose_name='Editável',
        help_text='Define se a configuração pode ser editada pela interface'
    )
    
    # Metadados
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Atualizado por'
    )
    
    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'
        ordering = ['categoria', 'chave']
        indexes = [
            models.Index(fields=['categoria']),
            models.Index(fields=['chave']),
            models.Index(fields=['editavel']),
        ]
    
    def __str__(self):
        return f'{self.categoria}.{self.chave}'
    
    def get_valor_tipado(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.tipo == 'integer':
            return int(self.valor)
        elif self.tipo == 'float':
            return float(self.valor)
        elif self.tipo == 'boolean':
            return self.valor.lower() in ['true', '1', 'yes', 'on']
        elif self.tipo == 'json':
            import json
            return json.loads(self.valor)
        elif self.tipo == 'date':
            from datetime import datetime
            return datetime.strptime(self.valor, '%Y-%m-%d').date()
        elif self.tipo == 'datetime':
            from datetime import datetime
            return datetime.fromisoformat(self.valor)
        else:
            return self.valor
