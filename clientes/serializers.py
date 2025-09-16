from rest_framework import serializers
from .models import Cliente, ParteEnvolvida, InteracaoCliente
from processos.models import Processo


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer básico para cliente (compatibilidade)"""
    tipo_pessoa_display = serializers.CharField(source='get_tipo_pessoa_display', read_only=True)
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome_razao_social', 'tipo_pessoa', 'tipo_pessoa_display',
            'cpf_cnpj', 'email', 'telefone', 'ativo'
        ]


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de clientes"""
    tipo_pessoa_display = serializers.CharField(source='get_tipo_pessoa_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    # Campos calculados
    total_processos = serializers.SerializerMethodField()
    processos_ativos = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome_razao_social', 'tipo_pessoa', 'tipo_pessoa_display',
            'cpf_cnpj', 'email', 'telefone', 'cidade', 'estado', 'estado_display',
            'total_processos', 'processos_ativos', 'ativo',
            'created_at', 'updated_at'
        ]
    
    def get_total_processos(self, obj):
        return obj.processos.count()
    
    def get_processos_ativos(self, obj):
        return obj.processos.filter(status='ativo').count()


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes completos do cliente"""
    tipo_pessoa_display = serializers.CharField(source='get_tipo_pessoa_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    # Campos calculados
    total_processos = serializers.SerializerMethodField()
    processos_ativos = serializers.SerializerMethodField()
    endereco_completo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'tipo_pessoa', 'tipo_pessoa_display', 'nome_razao_social',
            'cpf_cnpj', 'rg_ie', 'data_nascimento', 'profissao',
            'email', 'telefone', 'telefone_secundario', 'endereco', 'cidade', 
            'estado', 'estado_display', 'cep', 'endereco_completo', 'observacoes', 'ativo',
            'total_processos', 'processos_ativos', 'created_at', 'updated_at'
        ]
    
    def get_total_processos(self, obj):
        return obj.processos.count()
    
    def get_processos_ativos(self, obj):
        return obj.processos.filter(status='ativo').count()


class ClienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de clientes"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome_razao_social', 'cpf_cnpj', 'rg_ie', 
            'data_nascimento', 'profissao', 'email', 'telefone', 'telefone_secundario',
            'endereco', 'cidade', 'estado', 'cep', 'observacoes', 'ativo'
        ]
    
    def validate_cpf_cnpj(self, value):
        """Validar CPF/CNPJ"""
        if not value:
            return value
        
        # Remover caracteres especiais
        value = ''.join(filter(str.isdigit, value))
        
        # Validar tamanho
        if len(value) not in [11, 14]:
            raise serializers.ValidationError(
                "CPF deve ter 11 dígitos e CNPJ deve ter 14 dígitos."
            )
        
        # Verificar unicidade (exceto para o próprio objeto na atualização)
        queryset = Cliente.objects.filter(cpf_cnpj=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um cliente com este CPF/CNPJ."
            )
        
        return value


class ClienteResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para uso em outros endpoints"""
    tipo_pessoa_display = serializers.CharField(source='get_tipo_pessoa_display', read_only=True)
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome_razao_social', 'tipo_pessoa', 'tipo_pessoa_display',
            'cpf_cnpj', 'email', 'telefone', 'ativo'
        ]


class ParteEnvolvidaSerializer(serializers.ModelSerializer):
    """Serializer para partes envolvidas"""
    tipo_envolvimento_display = serializers.CharField(source='get_tipo_envolvimento_display', read_only=True)
    dados_oab = serializers.CharField(read_only=True)
    
    class Meta:
        model = ParteEnvolvida
        fields = [
            'id', 'nome', 'tipo_envolvimento', 'tipo_envolvimento_display',
            'cpf_cnpj', 'oab_numero', 'oab_uf', 'dados_oab', 'email', 'telefone',
            'endereco', 'observacoes', 'created_at'
        ]


class ClienteProcessosSerializer(serializers.ModelSerializer):
    """Serializer para processos do cliente"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    area_direito_display = serializers.CharField(source='get_area_direito_display', read_only=True)
    responsavel_nome = serializers.CharField(source='usuario_responsavel.get_full_name', read_only=True)
    
    class Meta:
        model = Processo
        fields = [
            'id', 'numero_processo', 'tipo_processo', 'area_direito',
            'area_direito_display', 'status', 'status_display', 'valor_causa',
            'data_inicio', 'data_encerramento', 'responsavel_nome',
            'created_at', 'updated_at'
        ]


class ClienteStatisticsSerializer(serializers.Serializer):
    """Serializer para estatísticas de clientes"""
    total_clientes = serializers.IntegerField()
    clientes_ativos = serializers.IntegerField()
    clientes_inativos = serializers.IntegerField()
    clientes_pf = serializers.IntegerField()
    clientes_pj = serializers.IntegerField()
    clientes_mes_atual = serializers.IntegerField()
    
    # Por estado
    por_estado = serializers.DictField()
    
    # Por cidade (top 10)
    por_cidade = serializers.DictField()
    
    # Clientes com mais processos
    top_clientes_processos = serializers.ListField()


class ClienteDashboardSerializer(serializers.Serializer):
    """Serializer para dados do dashboard de clientes"""
    total_clientes = serializers.IntegerField()
    novos_clientes_mes = serializers.IntegerField()
    clientes_ativos = serializers.IntegerField()
    clientes_com_processos_ativos = serializers.IntegerField()
    
    # Gráficos
    clientes_por_mes = serializers.ListField()
    clientes_por_tipo = serializers.DictField()
    clientes_por_estado = serializers.DictField()
    
    # Listas
    ultimos_clientes = ClienteListSerializer(many=True)
    clientes_sem_processos = ClienteListSerializer(many=True)


class InteracaoClienteSerializer(serializers.ModelSerializer):
    """Serializer para interações com clientes"""
    tipo_interacao_display = serializers.CharField(source='get_tipo_interacao_display', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True)
    
    class Meta:
        model = InteracaoCliente
        fields = [
            'id', 'cliente', 'cliente_nome', 'usuario', 'usuario_nome',
            'tipo_interacao', 'tipo_interacao_display', 'data_interacao',
            'assunto', 'descricao', 'processo_relacionado', 'created_at'
        ]
        read_only_fields = ['usuario']
    
    def create(self, validated_data):
        # Associar o usuário logado
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)