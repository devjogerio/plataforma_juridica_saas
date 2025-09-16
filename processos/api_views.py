from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Processo, Andamento, Prazo
from .serializers import (
    ProcessoListSerializer, ProcessoDetailSerializer, ProcessoCreateUpdateSerializer,
    AndamentoSerializer, PrazoSerializer, ProcessoStatisticsSerializer,
    ProcessoDashboardSerializer
)
from .filters import ProcessoFilter, AndamentoFilter, PrazoFilter
from core.permissions import IsOwnerOrReadOnly
from core.pagination import StandardResultsSetPagination


class ProcessoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de processos"""
    queryset = Processo.objects.select_related('cliente', 'responsavel').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProcessoFilter
    search_fields = ['numero_processo', 'cliente__nome_razao_social', 'tipo_processo']
    ordering_fields = ['data_inicio', 'created_at', 'numero_processo', 'valor_causa']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Retornar serializer apropriado para cada ação"""
        if self.action == 'list':
            return ProcessoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProcessoCreateUpdateSerializer
        return ProcessoDetailSerializer
    
    def get_queryset(self):
        """Filtrar processos baseado no usuário"""
        queryset = super().get_queryset()
        
        # Adicionar anotações para campos calculados
        queryset = queryset.annotate(
            total_andamentos=Count('andamentos'),
            total_prazos_pendentes=Count('prazos', filter=Q(prazos__status='pendente')),
            total_documentos=Count('documentos')
        )
        
        # Filtrar por responsável se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(responsavel=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Definir responsável padrão na criação"""
        if not serializer.validated_data.get('responsavel'):
            serializer.save(responsavel=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['get'])
    def andamentos(self, request, pk=None):
        """Listar andamentos do processo"""
        processo = self.get_object()
        andamentos = processo.andamentos.select_related('usuario').order_by('-data_andamento')
        
        # Paginação
        page = self.paginate_queryset(andamentos)
        if page is not None:
            serializer = AndamentoSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AndamentoSerializer(andamentos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adicionar_andamento(self, request, pk=None):
        """Adicionar andamento ao processo"""
        processo = self.get_object()
        serializer = AndamentoSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(processo=processo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def prazos(self, request, pk=None):
        """Listar prazos do processo"""
        processo = self.get_object()
        prazos = processo.prazos.select_related('responsavel').order_by('data_limite')
        
        # Filtrar por status se especificado
        status_filter = request.query_params.get('status')
        if status_filter:
            prazos = prazos.filter(status=status_filter)
        
        serializer = PrazoSerializer(prazos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adicionar_prazo(self, request, pk=None):
        """Adicionar prazo ao processo"""
        processo = self.get_object()
        serializer = PrazoSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(processo=processo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        """Listar documentos do processo"""
        from documentos.serializers import DocumentoResumoSerializer
        
        processo = self.get_object()
        documentos = processo.documentos.filter(ativo=True).order_by('-data_upload')
        
        serializer = DocumentoResumoSerializer(documentos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais de processos"""
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_processos = queryset.count()
        processos_ativos = queryset.filter(status='ativo').count()
        processos_suspensos = queryset.filter(status='suspenso').count()
        processos_encerrados = queryset.filter(status='encerrado').count()
        
        # Processos do mês atual
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        processos_mes_atual = queryset.filter(created_at__gte=inicio_mes).count()
        
        # Valor total das causas
        valor_total_causas = queryset.aggregate(total=Sum('valor_causa'))['total'] or 0
        
        # Média de dias em andamento
        processos_com_data = queryset.filter(data_inicio__isnull=False)
        if processos_com_data.exists():
            media_dias = processos_com_data.aggregate(
                media=Avg('dias_em_andamento')
            )['media'] or 0
        else:
            media_dias = 0
        
        # Por área do direito
        por_area_direito = dict(
            queryset.values('area_direito').annotate(
                count=Count('id')
            ).values_list('area_direito', 'count')
        )
        
        # Por responsável
        por_responsavel = dict(
            queryset.values('responsavel__first_name', 'responsavel__last_name').annotate(
                count=Count('id')
            ).values_list('responsavel__first_name', 'count')
        )
        
        # Prazos
        hoje = timezone.now().date()
        prazos_vencidos = Prazo.objects.filter(
            processo__in=queryset,
            status='pendente',
            data_limite__lt=hoje
        ).count()
        
        prazos_criticos = Prazo.objects.filter(
            processo__in=queryset,
            status='pendente',
            data_limite__lte=hoje + timedelta(days=3)
        ).count()
        
        prazos_proximos = Prazo.objects.filter(
            processo__in=queryset,
            status='pendente',
            data_limite__lte=hoje + timedelta(days=7)
        ).count()
        
        data = {
            'total_processos': total_processos,
            'processos_ativos': processos_ativos,
            'processos_suspensos': processos_suspensos,
            'processos_encerrados': processos_encerrados,
            'processos_mes_atual': processos_mes_atual,
            'valor_total_causas': valor_total_causas,
            'media_dias_andamento': round(media_dias, 1),
            'por_area_direito': por_area_direito,
            'por_responsavel': por_responsavel,
            'prazos_vencidos': prazos_vencidos,
            'prazos_criticos': prazos_criticos,
            'prazos_proximos': prazos_proximos,
        }
        
        serializer = ProcessoStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dados para dashboard de processos"""
        queryset = self.get_queryset()
        
        # Processos recentes (últimos 10)
        processos_recentes = queryset.order_by('-created_at')[:10]
        
        # Prazos críticos (próximos 3 dias)
        hoje = timezone.now().date()
        prazos_criticos = Prazo.objects.filter(
            processo__in=queryset,
            status='pendente',
            data_limite__lte=hoje + timedelta(days=3)
        ).select_related('processo', 'responsavel').order_by('data_limite')[:10]
        
        # Andamentos recentes (últimos 10)
        andamentos_recentes = Andamento.objects.filter(
            processo__in=queryset
        ).select_related('processo', 'usuario').order_by('-created_at')[:10]
        
        # Gráfico de processos por mês (últimos 12 meses)
        grafico_processos_mes = {}
        for i in range(12):
            data_inicio = timezone.now().replace(day=1) - timedelta(days=30*i)
            data_fim = data_inicio.replace(day=1) + timedelta(days=32)
            data_fim = data_fim.replace(day=1) - timedelta(days=1)
            
            count = queryset.filter(
                created_at__gte=data_inicio,
                created_at__lte=data_fim
            ).count()
            
            mes_nome = data_inicio.strftime('%b/%Y')
            grafico_processos_mes[mes_nome] = count
        
        # Gráfico por status
        grafico_processos_status = dict(
            queryset.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        # Gráfico por área
        grafico_processos_area = dict(
            queryset.values('area_direito').annotate(
                count=Count('id')
            ).values_list('area_direito', 'count')
        )
        
        # Obter estatísticas
        estatisticas_response = self.estatisticas(request)
        estatisticas = estatisticas_response.data
        
        data = {
            'processos_recentes': ProcessoListSerializer(
                processos_recentes, many=True, context={'request': request}
            ).data,
            'estatisticas': estatisticas,
            'prazos_criticos': PrazoSerializer(
                prazos_criticos, many=True, context={'request': request}
            ).data,
            'andamentos_recentes': AndamentoSerializer(
                andamentos_recentes, many=True, context={'request': request}
            ).data,
            'grafico_processos_mes': grafico_processos_mes,
            'grafico_processos_status': grafico_processos_status,
            'grafico_processos_area': grafico_processos_area,
        }
        
        serializer = ProcessoDashboardSerializer(data)
        return Response(serializer.data)


class AndamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de andamentos"""
    queryset = Andamento.objects.select_related('processo', 'usuario').all()
    serializer_class = AndamentoSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AndamentoFilter
    search_fields = ['tipo_andamento', 'descricao', 'processo__numero_processo']
    ordering_fields = ['data_andamento', 'created_at']
    ordering = ['-data_andamento']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filtrar andamentos baseado no usuário"""
        queryset = super().get_queryset()
        
        # Filtrar por processos do usuário se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Definir usuário automaticamente na criação"""
        serializer.save(usuario=self.request.user)


class PrazoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de prazos"""
    queryset = Prazo.objects.select_related('processo', 'responsavel').all()
    serializer_class = PrazoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PrazoFilter
    search_fields = ['tipo_prazo', 'descricao', 'processo__numero_processo']
    ordering_fields = ['data_limite', 'created_at']
    ordering = ['data_limite']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filtrar prazos baseado no usuário"""
        queryset = super().get_queryset()
        
        # Filtrar por processos do usuário se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def cumprir(self, request, pk=None):
        """Marcar prazo como cumprido"""
        prazo = self.get_object()
        
        if prazo.status == 'cumprido':
            return Response(
                {'error': 'Prazo já está marcado como cumprido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prazo.status = 'cumprido'
        prazo.data_cumprimento = timezone.now().date()
        prazo.save()
        
        serializer = self.get_serializer(prazo)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def criticos(self, request):
        """Listar prazos críticos (próximos 3 dias)"""
        hoje = timezone.now().date()
        prazos_criticos = self.get_queryset().filter(
            status='pendente',
            data_limite__lte=hoje + timedelta(days=3)
        ).order_by('data_limite')
        
        serializer = self.get_serializer(prazos_criticos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidos(self, request):
        """Listar prazos vencidos"""
        hoje = timezone.now().date()
        prazos_vencidos = self.get_queryset().filter(
            status='pendente',
            data_limite__lt=hoje
        ).order_by('data_limite')
        
        serializer = self.get_serializer(prazos_vencidos, many=True)
        return Response(serializer.data)