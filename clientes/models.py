import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .validators import validar_cpf, validar_cnpj, formatar_cpf, formatar_cnpj, limpar_documento


class Cliente(models.Model):
    """
    Modelo para gestão de clientes (Pessoa Física e Jurídica).
    Armazena informações completas dos clientes do escritório.
    """
    
    TIPO_PESSOA_CHOICES = [
        ('PF', _('Pessoa Física')),
        ('PJ', _('Pessoa Jurídica')),
    ]
    
    ESTADO_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
        ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
        ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]
    
    # Validadores
    cpf_validator = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message=_('CPF deve estar no formato: 000.000.000-00')
    )
    
    cnpj_validator = RegexValidator(
        regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
        message=_('CNPJ deve estar no formato: 00.000.000/0000-00')
    )
    
    telefone_validator = RegexValidator(
        regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
        message=_('Telefone deve estar no formato: (00) 0000-0000 ou (00) 00000-0000')
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do cliente')
    )
    
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES,
        verbose_name=_('Tipo de Pessoa'),
        help_text=_('Pessoa Física ou Jurídica')
    )
    
    nome_razao_social = models.CharField(
        max_length=255,
        verbose_name=_('Nome/Razão Social'),
        help_text=_('Nome completo (PF) ou Razão Social (PJ)')
    )
    
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name=_('CPF/CNPJ'),
        help_text=_('Documento de identificação')
    )
    
    rg_ie = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('RG/Inscrição Estadual'),
        help_text=_('RG (PF) ou Inscrição Estadual (PJ)')
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('E-mail'),
        help_text=_('Endereço de e-mail para contato')
    )
    
    telefone = models.CharField(
        max_length=20,
        validators=[telefone_validator],
        blank=True,
        null=True,
        verbose_name=_('Telefone'),
        help_text=_('Número de telefone principal')
    )
    
    telefone_secundario = models.CharField(
        max_length=20,
        validators=[telefone_validator],
        blank=True,
        null=True,
        verbose_name=_('Telefone Secundário')
    )
    
    endereco = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Endereço'),
        help_text=_('Endereço completo')
    )
    
    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Cidade')
    )
    
    estado = models.CharField(
        max_length=2,
        choices=ESTADO_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Estado')
    )
    
    cep = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('CEP'),
        help_text=_('Código de Endereçamento Postal')
    )
    
    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Nascimento'),
        help_text=_('Data de nascimento (PF) ou fundação (PJ)')
    )
    
    profissao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Profissão'),
        help_text=_('Profissão (PF) ou atividade principal (PJ)')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações'),
        help_text=_('Informações adicionais sobre o cliente')
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo'),
        help_text=_('Define se o cliente está ativo no sistema')
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
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['nome_razao_social']
        indexes = [
            models.Index(fields=['tipo_pessoa']),
            models.Index(fields=['nome_razao_social']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome_razao_social} ({self.get_tipo_pessoa_display()})"
    
    def clean(self):
        """Validação customizada do modelo."""
        super().clean()
        
        # Pula validação durante testes se a flag estiver definida
        if getattr(self, '_skip_validation', False):
            return
        
        if self.cpf_cnpj:
            # Remove formatação para validação
            documento_limpo = limpar_documento(self.cpf_cnpj)
            
            if self.tipo_pessoa == 'PF':
                try:
                    validar_cpf(documento_limpo)
                    # Armazena o CPF formatado
                    self.cpf_cnpj = formatar_cpf(documento_limpo)
                except ValidationError as e:
                    raise ValidationError({'cpf_cnpj': e.message})
            elif self.tipo_pessoa == 'PJ':
                try:
                    validar_cnpj(documento_limpo)
                    # Armazena o CNPJ formatado
                    self.cpf_cnpj = formatar_cnpj(documento_limpo)
                except ValidationError as e:
                    raise ValidationError({'cpf_cnpj': e.message})
    
    def save(self, *args, **kwargs):
        """Override do save para garantir validação antes de salvar."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def documento_principal(self):
        """Retorna o documento principal (CPF ou CNPJ) formatado."""
        return self.cpf_cnpj if self.cpf_cnpj else None
    
    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado."""
        partes = []
        if self.endereco:
            partes.append(self.endereco)
        if self.cidade:
            partes.append(self.cidade)
        if self.estado:
            partes.append(self.get_estado_display())
        if self.cep:
            partes.append(f"CEP: {self.cep}")
        
        return ', '.join(partes) if partes else ''


class ParteEnvolvida(models.Model):
    """
    Modelo para outras partes envolvidas nos processos.
    Representa advogados contrários, réus, testemunhas, peritos, etc.
    """
    
    TIPO_ENVOLVIMENTO_CHOICES = [
        ('reu', _('Réu')),
        ('advogado_contrario', _('Advogado Contrário')),
        ('testemunha', _('Testemunha')),
        ('perito', _('Perito')),
        ('assistente_tecnico', _('Assistente Técnico')),
        ('terceiro_interessado', _('Terceiro Interessado')),
        ('ministerio_publico', _('Ministério Público')),
        ('outro', _('Outro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome = models.CharField(
        max_length=255,
        verbose_name=_('Nome'),
        help_text=_('Nome completo da parte envolvida')
    )
    
    tipo_envolvimento = models.CharField(
        max_length=30,
        choices=TIPO_ENVOLVIMENTO_CHOICES,
        verbose_name=_('Tipo de Envolvimento')
    )
    
    cpf_cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        verbose_name=_('CPF/CNPJ')
    )
    
    oab_numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Número OAB'),
        help_text=_('Apenas para advogados')
    )
    
    oab_uf = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name=_('UF OAB')
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('E-mail')
    )
    
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Telefone')
    )
    
    endereco = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Endereço')
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
        verbose_name = _('Parte Envolvida')
        verbose_name_plural = _('Partes Envolvidas')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['tipo_envolvimento']),
            models.Index(fields=['nome']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_envolvimento_display()})"
    
    @property
    def is_advogado(self):
        """Verifica se a parte é um advogado."""
        return self.tipo_envolvimento == 'advogado_contrario'
    
    @property
    def dados_oab(self):
        """Retorna os dados da OAB formatados."""
        if self.oab_numero and self.oab_uf:
            return f"OAB/{self.oab_uf} {self.oab_numero}"
        return ''


class InteracaoCliente(models.Model):
    """
    Modelo para registrar interações com clientes (CRM básico).
    Mantém histórico de comunicações e anotações.
    """
    
    TIPO_INTERACAO_CHOICES = [
        ('ligacao', _('Ligação Telefônica')),
        ('email', _('E-mail')),
        ('reuniao', _('Reunião')),
        ('whatsapp', _('WhatsApp')),
        ('carta', _('Carta')),
        ('audiencia', _('Audiência')),
        ('outro', _('Outro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='interacoes',
        verbose_name=_('Cliente')
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        verbose_name=_('Usuário Responsável')
    )
    
    tipo_interacao = models.CharField(
        max_length=20,
        choices=TIPO_INTERACAO_CHOICES,
        verbose_name=_('Tipo de Interação')
    )
    
    data_interacao = models.DateTimeField(
        verbose_name=_('Data/Hora da Interação')
    )
    
    assunto = models.CharField(
        max_length=200,
        verbose_name=_('Assunto')
    )
    
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        help_text=_('Detalhes da interação')
    )
    
    processo_relacionado = models.ForeignKey(
        'processos.Processo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Processo Relacionado')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Interação com Cliente')
        verbose_name_plural = _('Interações com Clientes')
        ordering = ['-data_interacao']
        indexes = [
            models.Index(fields=['cliente', '-data_interacao']),
            models.Index(fields=['tipo_interacao']),
        ]
    
    def __str__(self):
        return f"{self.cliente.nome_razao_social} - {self.assunto} ({self.data_interacao.strftime('%d/%m/%Y')})"
