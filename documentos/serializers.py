from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Documento
from processos.models import Processo
from usuarios.serializers import UsuarioResumoSerializer
from processos.serializers import ProcessoListSerializer

User = get_user_model()


class DocumentoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de documentos (campos resumidos)"""
    processo_numero = serializers.CharField(source='processo.numero_processo', read_only=True)
    usuario_upload_nome = serializers.CharField(source='usuario_upload.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tamanho_arquivo = serializers.IntegerField(source='arquivo.size', read_only=True)
    extensao = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'nome', 'tipo', 'tipo_display', 'processo',
            'processo_numero', 'tamanho_arquivo', 'extensao',
            'data_upload', 'usuario_upload_nome', 'versao',
            'confidencial', 'ativo', 'created_at', 'updated_at'
        ]
    
    def get_extensao(self, obj):
        """Obter extensão do arquivo"""
        if obj.arquivo and obj.arquivo.name:
            return obj.arquivo.name.split('.')[-1].lower()
        return None


class DocumentoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes completos do documento"""
    processo = ProcessoListSerializer(read_only=True)
    usuario_upload = UsuarioResumoSerializer(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tamanho_arquivo = serializers.IntegerField(source='arquivo.size', read_only=True)
    url_download = serializers.SerializerMethodField()
    extensao = serializers.SerializerMethodField()
    mime_type = serializers.SerializerMethodField()
    
    # Campos calculados
    total_versoes = serializers.IntegerField(read_only=True)
    total_downloads = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Documento
        fields = [
            'id', 'nome', 'descricao', 'tipo', 'tipo_display',
            'processo', 'arquivo', 'tamanho_arquivo', 'extensao',
            'mime_type', 'hash_arquivo', 'versao', 'confidencial',
            'ativo', 'data_upload', 'usuario_upload', 'observacoes_versao',
            'url_download', 'total_versoes', 'total_downloads',
            'created_at', 'updated_at'
        ]
    
    def get_url_download(self, obj):
        """URL para download do documento"""
        request = self.context.get('request')
        if request and obj.arquivo:
            return request.build_absolute_uri(f'/api/documentos/{obj.id}/download/')
        return None
    
    def get_extensao(self, obj):
        """Obter extensão do arquivo"""
        if obj.arquivo and obj.arquivo.name:
            return obj.arquivo.name.split('.')[-1].lower()
        return None
    
    def get_mime_type(self, obj):
        """Obter MIME type do arquivo"""
        import mimetypes
        if obj.arquivo and obj.arquivo.name:
            mime_type, _ = mimetypes.guess_type(obj.arquivo.name)
            return mime_type
        return None


class DocumentoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de documentos"""
    arquivo = serializers.FileField(required=True)
    
    class Meta:
        model = Documento
        fields = [
            'nome', 'descricao', 'tipo', 'processo', 'arquivo',
            'confidencial', 'observacoes_versao'
        ]
    
    def validate_arquivo(self, value):
        """Validar arquivo"""
        # Verificar tamanho (50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Arquivo muito grande. Tamanho máximo: {max_size // (1024*1024)}MB"
            )
        
        # Verificar extensão
        allowed_extensions = [
            'pdf', 'doc', 'docx', 'xls', 'xlsx',
            'jpg', 'jpeg', 'png', 'txt', 'rtf'
        ]
        
        extension = value.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Extensão '{extension}' não permitida. "
                f"Extensões permitidas: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate_nome(self, value):
        """Validar nome do documento"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nome deve ter pelo menos 3 caracteres."
            )
        return value.strip()
    
    def create(self, validated_data):
        """Criar documento com usuário e versão"""
        validated_data['usuario_upload'] = self.context['request'].user
        validated_data['versao'] = 1
        
        # Gerar hash do arquivo
        arquivo = validated_data['arquivo']
        validated_data['hash_arquivo'] = self._generate_file_hash(arquivo)
        
        return super().create(validated_data)
    
    def _generate_file_hash(self, arquivo):
        """Gerar hash SHA-256 do arquivo"""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        for chunk in arquivo.chunks():
            hash_sha256.update(chunk)
        
        # Reset file pointer
        arquivo.seek(0)
        
        return hash_sha256.hexdigest()


class DocumentoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de documentos (apenas metadados)"""
    
    class Meta:
        model = Documento
        fields = [
            'nome', 'descricao', 'tipo', 'processo',
            'confidencial', 'ativo'
        ]
    
    def validate_nome(self, value):
        """Validar nome do documento"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nome deve ter pelo menos 3 caracteres."
            )
        return value.strip()


class NovaVersaoSerializer(serializers.ModelSerializer):
    """Serializer para criar nova versão de documento"""
    arquivo = serializers.FileField(required=True)
    
    class Meta:
        model = Documento
        fields = ['arquivo', 'observacoes_versao']
    
    def validate_arquivo(self, value):
        """Validar arquivo da nova versão"""
        # Verificar tamanho (50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Arquivo muito grande. Tamanho máximo: {max_size // (1024*1024)}MB"
            )
        
        # Verificar se é o mesmo tipo de arquivo
        documento_original = self.context.get('documento_original')
        if documento_original:
            extensao_original = documento_original.arquivo.name.split('.')[-1].lower()
            extensao_nova = value.name.split('.')[-1].lower()
            
            if extensao_original != extensao_nova:
                raise serializers.ValidationError(
                    f"Nova versão deve ter a mesma extensão do documento original (.{extensao_original})"
                )
        
        return value
    
    def create(self, validated_data):
        """Criar nova versão do documento"""
        documento_original = self.context['documento_original']
        
        # Criar nova versão
        nova_versao = Documento.objects.create(
            nome=documento_original.nome,
            descricao=documento_original.descricao,
            tipo=documento_original.tipo,
            processo=documento_original.processo,
            arquivo=validated_data['arquivo'],
            confidencial=documento_original.confidencial,
            usuario_upload=self.context['request'].user,
            versao=documento_original.versao + 1,
            observacoes_versao=validated_data.get('observacoes_versao', ''),
            hash_arquivo=self._generate_file_hash(validated_data['arquivo']),
            documento_pai=documento_original.documento_pai or documento_original
        )
        
        return nova_versao
    
    def _generate_file_hash(self, arquivo):
        """Gerar hash SHA-256 do arquivo"""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        for chunk in arquivo.chunks():
            hash_sha256.update(chunk)
        
        # Reset file pointer
        arquivo.seek(0)
        
        return hash_sha256.hexdigest()


class DocumentoVersaoSerializer(serializers.ModelSerializer):
    """Serializer para versões do documento"""
    usuario_upload_nome = serializers.CharField(source='usuario_upload.get_full_name', read_only=True)
    tamanho_arquivo = serializers.IntegerField(source='arquivo.size', read_only=True)
    url_download = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'versao', 'arquivo', 'tamanho_arquivo',
            'data_upload', 'usuario_upload_nome', 'observacoes_versao',
            'hash_arquivo', 'url_download', 'created_at'
        ]
    
    def get_url_download(self, obj):
        """URL para download da versão"""
        request = self.context.get('request')
        if request and obj.arquivo:
            return request.build_absolute_uri(f'/api/documentos/{obj.id}/download/')
        return None


class DocumentoStatisticsSerializer(serializers.Serializer):
    """Serializer para estatísticas de documentos"""
    total_documentos = serializers.IntegerField()
    documentos_mes_atual = serializers.IntegerField()
    tamanho_total = serializers.IntegerField()
    documentos_confidenciais = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
    
    # Por tipo
    por_tipo = serializers.DictField()
    
    # Por extensão
    por_extensao = serializers.DictField()
    
    # Por usuário (top uploaders)
    top_uploaders = serializers.ListField()
    
    # Documentos mais baixados
    mais_baixados = serializers.ListField()


class DocumentoResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para uso em outros endpoints"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tamanho_arquivo = serializers.IntegerField(source='arquivo.size', read_only=True)
    extensao = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'nome', 'tipo', 'tipo_display', 'tamanho_arquivo',
            'extensao', 'data_upload', 'versao', 'confidencial'
        ]
    
    def get_extensao(self, obj):
        """Obter extensão do arquivo"""
        if obj.arquivo and obj.arquivo.name:
            return obj.arquivo.name.split('.')[-1].lower()
        return None


class DocumentoUploadResponseSerializer(serializers.Serializer):
    """Serializer para resposta de upload"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    documento = DocumentoDetailSerializer(required=False)
    errors = serializers.DictField(required=False)