from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Processo, Andamento, Prazo
from clientes.models import Cliente
from clientes.serializers import ClienteSerializer
from usuarios.serializers import UsuarioSerializer

User = get_user_model()


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de processos (campos resumidos)"""
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    area_direito_display = serializers.CharField(source='get_area_direito_display', read_only=True)
    total_andamentos = serializers.IntegerField(read_only=True)
    total_prazos_pendentes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Processo
        fields = [
            'id', 'numero_processo', 'cliente_nome', 'tipo_processo',
            'area_direito', 'area_direito_display', 'status', 'status_display',
            'valor_causa', 'data_inicio', 'responsavel_nome', 'total_andamentos',
            'total_prazos_pendentes', 'created_at', 'updated_at'
        ]


class ProcessoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes completos do processo"""
    cliente = ClienteSerializer(read_only=True)
    responsavel = UsuarioSerializer(read_only=True)
    cliente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        source='cliente',
        write_only=True
    )
    responsavel_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='responsavel',
        write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    area_direito_display = serializers.CharField(source='get_area_direito_display', read_only=True)
    
    # Campos calculados
    total_andamentos = serializers.IntegerField(read_only=True)
    total_prazos_pendentes = serializers.IntegerField(read_only=True)
    total_documentos = serializers.IntegerField(read_only=True)
    dias_em_andamento = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Processo
        fields = [
            'id', 'numero_processo', 'cliente', 'cliente_id', 'tipo_processo',
            'area_direito', 'area_direito_display', 'status', 'status_display',
            'valor_causa', 'data_inicio', 'data_encerramento', 'comarca', 'vara',
            'juiz', 'observacoes', 'responsavel', 'responsavel_id',
            'total_andamentos', 'total_prazos_pendentes', 'total_documentos',
            'dias_em_andamento', 'created_at', 'updated_at'
        ]
    
    def validate_numero_processo(self, value):
        """Validar formato do número do processo"""
        import re
        pattern = r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Número do processo deve seguir o formato: 1234567-12.2023.1.23.4567"
            )
        return value
    
    def validate(self, data):
        """Validações gerais"""
        if data.get('data_encerramento') and data.get('data_inicio'):
            if data['data_encerramento'] < data['data_inicio']:
                raise serializers.ValidationError(
                    "Data de encerramento não pode ser anterior à data de início."
                )
        return data


class ProcessoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de processos"""
    
    class Meta:
        model = Processo
        fields = [
            'numero_processo', 'cliente', 'tipo_processo', 'area_direito',
            'status', 'valor_causa', 'data_inicio', 'data_encerramento',
            'comarca', 'vara', 'juiz', 'observacoes', 'responsavel'
        ]
    
    def validate_numero_processo(self, value):
        """Validar formato e unicidade do número do processo"""
        import re
        pattern = r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Número do processo deve seguir o formato: 1234567-12.2023.1.23.4567"
            )
        
        # Verificar unicidade (exceto para o próprio objeto na atualização)
        queryset = Processo.objects.filter(numero_processo=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um processo com este número."
            )
        
        return value


class AndamentoSerializer(serializers.ModelSerializer):
    """Serializer para andamentos do processo"""
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_processo', read_only=True)
    
    class Meta:
        model = Andamento
        fields = [
            'id', 'processo', 'processo_numero', 'data_andamento',
            'tipo_andamento', 'descricao', 'usuario', 'usuario_nome',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['usuario']
    
    def validate_data_andamento(self, value):
        """Validar se a data do andamento não é futura"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Data do andamento não pode ser futura."
            )
        return value
    
    def create(self, validated_data):
        """Definir usuário automaticamente na criação"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class PrazoSerializer(serializers.ModelSerializer):
    """Serializer para prazos do processo"""
    processo_numero = serializers.CharField(source='processo.numero_processo', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Prazo
        fields = [
            'id', 'processo', 'processo_numero', 'tipo_prazo', 'descricao',
            'data_limite', 'status', 'status_display', 'responsavel',
            'responsavel_nome', 'data_cumprimento', 'observacoes',
            'dias_restantes', 'created_at', 'updated_at'
        ]
    
    def validate_data_limite(self, value):
        """Validar se a data limite não é muito no passado"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Permitir datas até 30 dias no passado (para casos excepcionais)
        limite_passado = timezone.now().date() - timedelta(days=30)
        if value < limite_passado:
            raise serializers.ValidationError(
                "Data limite não pode ser anterior a 30 dias atrás."
            )
        return value
    
    def validate(self, data):
        """Validações gerais"""
        if data.get('status') == 'cumprido' and not data.get('data_cumprimento'):
            data['data_cumprimento'] = timezone.now().date()
        
        if data.get('data_cumprimento') and data.get('data_limite'):
            if data['data_cumprimento'] < data['data_limite']:
                # Prazo cumprido antes do vencimento - OK
                pass
        
        return data


class ProcessoStatisticsSerializer(serializers.Serializer):
    """Serializer para estatísticas de processos"""
    total_processos = serializers.IntegerField()
    processos_ativos = serializers.IntegerField()
    processos_suspensos = serializers.IntegerField()
    processos_encerrados = serializers.IntegerField()
    processos_mes_atual = serializers.IntegerField()
    valor_total_causas = serializers.DecimalField(max_digits=15, decimal_places=2)
    media_dias_andamento = serializers.FloatField()
    
    # Por área do direito
    por_area_direito = serializers.DictField()
    
    # Por responsável
    por_responsavel = serializers.DictField()
    
    # Prazos
    prazos_vencidos = serializers.IntegerField()
    prazos_criticos = serializers.IntegerField()
    prazos_proximos = serializers.IntegerField()


class ProcessoDashboardSerializer(serializers.Serializer):
    """Serializer para dados do dashboard de processos"""
    processos_recentes = ProcessoListSerializer(many=True)
    estatisticas = ProcessoStatisticsSerializer()
    prazos_criticos = PrazoSerializer(many=True)
    andamentos_recentes = AndamentoSerializer(many=True)
    
    # Gráficos
    grafico_processos_mes = serializers.DictField()
    grafico_processos_status = serializers.DictField()
    grafico_processos_area = serializers.DictField()