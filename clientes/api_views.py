from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Cliente
from .serializers import (
    ClienteListSerializer, ClienteDetailSerializer, ClienteCreateUpdateSerializer,
    ClienteProcessosSerializer, ClienteStatisticsSerializer, ClienteDashboardSerializer
)
from .filters import ClienteFilter
from core.permissions import IsClienteOwnerOrReadOnly
from core.pagination import StandardResultsSetPagination


class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de clientes"""
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated, IsClienteOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClienteFilter
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'email', 'telefone']
    ordering_fields = ['nome_razao_social', 'created_at', 'cidade']
    ordering = ['nome_razao_social']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Retornar serializer apropriado para cada ação"""
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClienteCreateUpdateSerializer
        return ClienteDetailSerializer
    
    def get_queryset(self):
        """Retornar todos os clientes com anotações calculadas"""
        queryset = super().get_queryset()
        
        # Adicionar anotações para campos calculados
        queryset = queryset.annotate(
            total_processos=Count('processos'),
            processos_ativos=Count('processos', filter=Q(processos__status='ativo')),
            processos_encerrados=Count('processos', filter=Q(processos__status='encerrado')),
            valor_total_causas=Sum('processos__valor_causa')
        )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def processos(self, request, pk=None):
        """Listar processos do cliente"""
        cliente = self.get_object()
        processos = cliente.processos.select_related('responsavel').all()
        
        # Filtrar por responsável se não for staff
        if not request.user.is_staff:
            processos = processos.filter(responsavel=request.user)
        
        # Adicionar campos calculados
        from django.utils import timezone
        for processo in processos:
            if processo.data_inicio:
                dias_andamento = (timezone.now().date() - processo.data_inicio).days
                processo.dias_em_andamento = dias_andamento
            else:
                processo.dias_em_andamento = 0
        
        # Paginação
        page = self.paginate_queryset(processos)
        if page is not None:
            serializer = ClienteProcessosSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ClienteProcessosSerializer(processos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Estatísticas específicas do cliente"""
        cliente = self.get_object()
        processos = cliente.processos.all()
        
        # Filtrar por responsável se não for staff
        if not request.user.is_staff:
            processos = processos.filter(responsavel=request.user)
        
        # Estatísticas básicas
        total_processos = processos.count()
        processos_ativos = processos.filter(status='ativo').count()
        processos_encerrados = processos.filter(status='encerrado').count()
        valor_total_causas = processos.aggregate(total=Sum('valor_causa'))['total'] or 0
        
        # Processos por área do direito
        por_area_direito = dict(
            processos.values('area_direito').annotate(
                count=Count('id')
            ).values_list('area_direito', 'count')
        )
        
        # Andamentos recentes
        from processos.models import Andamento
        andamentos_recentes = Andamento.objects.filter(
            processo__in=processos
        ).order_by('-created_at')[:5]
        
        # Prazos pendentes
        from processos.models import Prazo
        prazos_pendentes = Prazo.objects.filter(
            processo__in=processos,
            status='pendente'
        ).count()
        
        data = {
            'total_processos': total_processos,
            'processos_ativos': processos_ativos,
            'processos_encerrados': processos_encerrados,
            'valor_total_causas': valor_total_causas,
            'por_area_direito': por_area_direito,
            'prazos_pendentes': prazos_pendentes,
            'andamentos_recentes_count': andamentos_recentes.count(),
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def estatisticas_gerais(self, request):
        """Estatísticas gerais de clientes"""
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_clientes = queryset.count()
        clientes_ativos = queryset.filter(ativo=True).count()
        clientes_inativos = queryset.filter(ativo=False).count()
        clientes_pf = queryset.filter(tipo_pessoa='PF').count()
        clientes_pj = queryset.filter(tipo_pessoa='PJ').count()
        
        # Clientes do mês atual
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        clientes_mes_atual = queryset.filter(created_at__gte=inicio_mes).count()
        
        # Por estado
        por_estado = dict(
            queryset.values('uf').annotate(
                count=Count('id')
            ).values_list('uf', 'count')
        )
        
        # Por cidade (top 10)
        por_cidade = dict(
            queryset.values('cidade').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('cidade', 'count')
        )
        
        # Clientes com mais processos
        top_clientes_processos = list(
            queryset.annotate(
                total_proc=Count('processos')
            ).filter(total_proc__gt=0).order_by('-total_proc')[:10].values(
                'id', 'nome_razao_social', 'total_proc'
            )
        )
        
        data = {
            'total_clientes': total_clientes,
            'clientes_ativos': clientes_ativos,
            'clientes_inativos': clientes_inativos,
            'clientes_pf': clientes_pf,
            'clientes_pj': clientes_pj,
            'clientes_mes_atual': clientes_mes_atual,
            'por_estado': por_estado,
            'por_cidade': por_cidade,
            'top_clientes_processos': top_clientes_processos,
        }
        
        serializer = ClienteStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dados para dashboard de clientes"""
        queryset = self.get_queryset()
        
        # Clientes recentes (últimos 10)
        clientes_recentes = queryset.order_by('-created_at')[:10]
        
        # Gráfico de clientes por mês (últimos 12 meses)
        grafico_clientes_mes = {}
        for i in range(12):
            data_inicio = timezone.now().replace(day=1) - timedelta(days=30*i)
            data_fim = data_inicio.replace(day=1) + timedelta(days=32)
            data_fim = data_fim.replace(day=1) - timedelta(days=1)
            
            count = queryset.filter(
                created_at__gte=data_inicio,
                created_at__lte=data_fim
            ).count()
            
            mes_nome = data_inicio.strftime('%b/%Y')
            grafico_clientes_mes[mes_nome] = count
        
        # Gráfico por tipo
        grafico_clientes_tipo = dict(
            queryset.values('tipo_pessoa').annotate(
                count=Count('id')
            ).values_list('tipo_pessoa', 'count')
        )
        
        # Gráfico por estado (top 10)
        grafico_clientes_estado = dict(
            queryset.values('uf').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('uf', 'count')
        )
        
        # Obter estatísticas
        estatisticas_response = self.estatisticas_gerais(request)
        estatisticas = estatisticas_response.data
        
        data = {
            'clientes_recentes': ClienteListSerializer(
                clientes_recentes, many=True, context={'request': request}
            ).data,
            'estatisticas': estatisticas,
            'grafico_clientes_mes': grafico_clientes_mes,
            'grafico_clientes_tipo': grafico_clientes_tipo,
            'grafico_clientes_estado': grafico_clientes_estado,
        }
        
        serializer = ClienteDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca rápida de clientes"""
        query = request.query_params.get('q', '')
        
        if len(query) < 2:
            return Response({
                'error': 'Query deve ter pelo menos 2 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(nome_razao_social__icontains=query) |
            Q(cpf_cnpj__icontains=query) |
            Q(email__icontains=query)
        )[:10]  # Limitar a 10 resultados
        
        from .serializers import ClienteResumoSerializer
        serializer = ClienteResumoSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)