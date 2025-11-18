import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
import hashlib


def upload_to_processo(instance, filename):
    """
    Função para definir o caminho de upload dos documentos.
    Organiza por processo e tipo de documento.
    """
    # Sanitiza o nome do arquivo
    nome_arquivo = filename.replace(' ', '_')
    
    # Cria estrutura de pastas: documentos/processo_id/tipo/arquivo
    return f"documentos/{instance.processo.id}/{instance.tipo_documento}/{nome_arquivo}"


class TipoDocumento(models.Model):
    """
    Modelo para categorização de tipos de documentos.
    Permite configurar diferentes categorias de documentos.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Nome do Tipo'),
        help_text=_('Nome da categoria de documento')
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição detalhada do tipo de documento')
    )
    
    extensoes_permitidas = models.CharField(
        max_length=200,
        default='pdf,doc,docx,jpg,jpeg,png,txt',
        verbose_name=_('Extensões Permitidas'),
        help_text=_('Extensões de arquivo permitidas, separadas por vírgula')
    )
    
    tamanho_maximo = models.PositiveIntegerField(
        default=52428800,  # 50MB
        verbose_name=_('Tamanho Máximo (bytes)'),
        help_text=_('Tamanho máximo do arquivo em bytes')
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Tipo de Documento')
        verbose_name_plural = _('Tipos de Documentos')
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    @property
    def extensoes_lista(self):
        """Retorna as extensões permitidas como lista."""
        return [ext.strip().lower() for ext in self.extensoes_permitidas.split(',')]
    
    @property
    def tamanho_maximo_mb(self):
        """Retorna o tamanho máximo em MB."""
        return round(self.tamanho_maximo / 1024 / 1024, 2)


class Documento(models.Model):
    """
    Modelo principal para gestão de documentos.
    Armazena metadados e referência aos arquivos físicos.
    """
    
    STATUS_CHOICES = [
        ('ativo', _('Ativo')),
        ('arquivado', _('Arquivado')),
        ('excluido', _('Excluído')),
    ]
    
    CONFIDENCIALIDADE_CHOICES = [
        ('publica', _('Pública')),
        ('interna', _('Interna')),
        ('confidencial', _('Confidencial')),
        ('secreta', _('Secreta')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do documento')
    )
    
    processo = models.ForeignKey(
        'processos.Processo',
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name=_('Processo')
    )
    
    tipo_documento = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Documento')
    )
    
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name=_('Nome do Arquivo'),
        help_text=_('Nome original do arquivo')
    )
    
    arquivo = models.FileField(
        upload_to=upload_to_processo,
        verbose_name=_('Arquivo'),
        help_text=_('Arquivo digital do documento')
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
    
    hash_arquivo = models.CharField(
        max_length=64,
        verbose_name=_('Hash do Arquivo'),
        help_text=_('Hash SHA-256 para verificação de integridade')
    )
    
    extensao = models.CharField(
        max_length=10,
        verbose_name=_('Extensão'),
        help_text=_('Extensão do arquivo')
    )
    
    confidencialidade = models.CharField(
        max_length=15,
        choices=CONFIDENCIALIDADE_CHOICES,
        default='interna',
        verbose_name=_('Nível de Confidencialidade')
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name=_('Status')
    )
    
    versao = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Versão'),
        help_text=_('Número da versão do documento')
    )
    
    documento_pai = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='versoes',
        verbose_name=_('Documento Pai'),
        help_text=_('Documento original (para controle de versões)')
    )
    
    palavras_chave = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Palavras-chave'),
        help_text=_('Palavras-chave para busca, separadas por vírgula')
    )
    
    data_documento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data do Documento'),
        help_text=_('Data de criação/emissão do documento')
    )
    
    usuario_upload = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário que fez Upload')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Upload')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Data de Atualização')
    )
    
    class Meta:
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processo', '-created_at']),
            models.Index(fields=['tipo_documento']),
            models.Index(fields=['status']),
            models.Index(fields=['hash_arquivo']),
            models.Index(fields=['usuario_upload']),
        ]
    
    def __str__(self):
        return f"{self.nome_arquivo} - {self.processo.numero_processo}"
    
    @property
    def nome(self):
        return self.nome_arquivo
    
    @nome.setter
    def nome(self, value):
        self.nome_arquivo = value
    
    @property
    def data_upload(self):
        return self.created_at
    
    @property
    def tipo(self):
        try:
            return self.tipo_documento.nome
        except Exception:
            return None
    
    def save(self, *args, **kwargs):
        """Override do save para calcular metadados automaticamente."""
        if self.arquivo:
            # Calcula o tamanho do arquivo
            self.tamanho_arquivo = self.arquivo.size
            
            # Extrai a extensão
            self.extensao = os.path.splitext(self.arquivo.name)[1].lower().replace('.', '')
            
            # Calcula o hash do arquivo
            if not self.hash_arquivo:
                self.hash_arquivo = self._calcular_hash()
            
            # Define o nome do arquivo se não foi fornecido
            if not self.nome_arquivo:
                self.nome_arquivo = os.path.basename(self.arquivo.name)
        
        super().save(*args, **kwargs)
    
    def _calcular_hash(self):
        """Calcula o hash SHA-256 do arquivo."""
        hash_sha256 = hashlib.sha256()
        
        # Lê o arquivo em chunks para não sobrecarregar a memória
        self.arquivo.seek(0)
        for chunk in iter(lambda: self.arquivo.read(4096), b""):
            hash_sha256.update(chunk)
        self.arquivo.seek(0)
        
        return hash_sha256.hexdigest()
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado."""
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} bytes"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"
    
    @property
    def url_download(self):
        """Retorna a URL para download do arquivo."""
        if self.arquivo:
            return self.arquivo.url
        return None
    
    @property
    def is_imagem(self):
        """Verifica se o documento é uma imagem."""
        extensoes_imagem = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
        return self.extensao.lower() in extensoes_imagem
    
    @property
    def is_pdf(self):
        """Verifica se o documento é um PDF."""
        return self.extensao.lower() == 'pdf'
    
    def pode_ser_visualizado_por(self, usuario):
        """Verifica se o usuário pode visualizar o documento."""
        # Administradores podem ver tudo
        if usuario.is_administrador:
            return True
        
        # Responsável pelo processo pode ver
        if usuario == self.processo.usuario_responsavel:
            return True
        
        # Cliente pode ver apenas documentos não confidenciais de seus processos
        if usuario.is_cliente and self.processo.cliente.email == usuario.email:
            return self.confidencialidade in ['publica', 'interna']
        
        return False
    
    def criar_nova_versao(self, arquivo, usuario, descricao=None):
        """Cria uma nova versão do documento."""
        nova_versao = Documento(
            processo=self.processo,
            tipo_documento=self.tipo_documento,
            arquivo=arquivo,
            descricao=descricao or self.descricao,
            confidencialidade=self.confidencialidade,
            documento_pai=self.documento_pai or self,
            versao=(self.documento_pai or self).versoes.count() + 1,
            palavras_chave=self.palavras_chave,
            data_documento=self.data_documento,
            usuario_upload=usuario
        )
        nova_versao.save()
        return nova_versao


class HistoricoAcesso(models.Model):
    """
    Modelo para registrar acessos aos documentos.
    Mantém auditoria de quem acessou quais documentos.
    """
    
    ACAO_CHOICES = [
        ('visualizacao', _('Visualização')),
        ('download', _('Download')),
        ('compartilhamento', _('Compartilhamento')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='historico_acessos',
        verbose_name=_('Documento')
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        verbose_name=_('Usuário')
    )
    
    acao = models.CharField(
        max_length=20,
        choices=ACAO_CHOICES,
        verbose_name=_('Ação')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=_('Endereço IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User Agent')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data/Hora')
    )
    
    class Meta:
        verbose_name = _('Histórico de Acesso')
        verbose_name_plural = _('Históricos de Acesso')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['documento', '-timestamp']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['acao']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_acao_display()} - {self.documento.nome_arquivo}"


class CompartilhamentoDocumento(models.Model):
    """
    Modelo para controlar compartilhamento de documentos.
    Permite compartilhar documentos com usuários específicos ou externos.
    """
    
    TIPO_COMPARTILHAMENTO_CHOICES = [
        ('interno', _('Usuário Interno')),
        ('externo', _('E-mail Externo')),
        ('link_publico', _('Link Público')),
    ]
    
    PERMISSAO_CHOICES = [
        ('visualizar', _('Apenas Visualizar')),
        ('download', _('Visualizar e Download')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='compartilhamentos',
        verbose_name=_('Documento')
    )
    
    tipo_compartilhamento = models.CharField(
        max_length=15,
        choices=TIPO_COMPARTILHAMENTO_CHOICES,
        verbose_name=_('Tipo de Compartilhamento')
    )
    
    usuario_interno = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Usuário Interno')
    )
    
    email_externo = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('E-mail Externo')
    )
    
    permissao = models.CharField(
        max_length=15,
        choices=PERMISSAO_CHOICES,
        default='visualizar',
        verbose_name=_('Permissão')
    )
    
    token_acesso = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=_('Token de Acesso'),
        help_text=_('Token único para acesso ao documento')
    )
    
    data_expiracao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Data de Expiração'),
        help_text=_('Data limite para acesso (opcional)')
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
    )
    
    usuario_compartilhou = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='compartilhamentos_criados',
        verbose_name=_('Usuário que Compartilhou')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Compartilhamento de Documento')
        verbose_name_plural = _('Compartilhamentos de Documentos')
        ordering = ['-created_at']
    
    def __str__(self):
        destinatario = self.usuario_interno.username if self.usuario_interno else self.email_externo
        return f"{self.documento.nome_arquivo} → {destinatario}"
    
    def save(self, *args, **kwargs):
        """Gera token de acesso automaticamente."""
        if not self.token_acesso:
            self.token_acesso = self._gerar_token()
        super().save(*args, **kwargs)
    
    def _gerar_token(self):
        """Gera um token único para acesso."""
        import secrets
        return secrets.token_urlsafe(32)
    
    @property
    def is_expirado(self):
        """Verifica se o compartilhamento está expirado."""
        if not self.data_expiracao:
            return False
        
        from django.utils import timezone
        return timezone.now() > self.data_expiracao
    
    @property
    def url_acesso(self):
        """Retorna a URL de acesso ao documento compartilhado."""
        from django.urls import reverse
        return reverse('documentos:acesso_compartilhado', kwargs={'token': self.token_acesso})
