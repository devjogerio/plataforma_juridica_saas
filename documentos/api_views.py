from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import HttpResponse, Http404
from datetime import timedelta
import mimetypes

from .models import Documento
from .serializers import (
    DocumentoListSerializer, DocumentoDetailSerializer, DocumentoCreateSerializer,
    DocumentoUpdateSerializer, NovaVersaoSerializer, DocumentoVersaoSerializer,
    DocumentoStatisticsSerializer, DocumentoUploadResponseSerializer
)
from .filters import DocumentoFilter
from core.permissions import IsDocumentoOwnerOrReadOnly
from core.pagination import DocumentosPagination


class DocumentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de documentos"""
    queryset = Documento.objects.select_related('processo', 'usuario_upload').all()
    permission_classes = [IsAuthenticated, IsDocumentoOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentoFilter
    search_fields = ['nome', 'descricao', 'processo__numero_processo']
    ordering_fields = ['nome', 'data_upload', 'versao', 'arquivo__size']
    ordering = ['-data_upload']
    pagination_class = DocumentosPagination
    
    def get_serializer_class(self):
        """Retornar serializer apropriado para cada ação"""
        if self.action == 'list':
            return DocumentoListSerializer
        elif self.action == 'create':
            return DocumentoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentoUpdateSerializer
        return DocumentoDetailSerializer
    
    def get_queryset(self):
        """Filtrar documentos baseado no usuário e permissões"""
        queryset = super().get_queryset()
        
        # Adicionar anotações para campos calculados
        queryset = queryset.annotate(
            total_versoes=Count('versoes') + 1,  # +1 para incluir o próprio documento
            total_downloads=Count('downloads')
        )
        
        # Filtrar documentos baseado nas permissões
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(processo__responsavel=self.request.user) |
                Q(usuario_upload=self.request.user) |
                Q(confidencial=False)  # Documentos não confidenciais são visíveis
            ).distinct()
        
        # Filtrar apenas documentos ativos por padrão
        if not self.request.query_params.get('incluir_inativos'):
            queryset = queryset.filter(ativo=True)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Upload de documento com resposta personalizada"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            documento = serializer.save()
            
            response_data = {
                'success': True,
                'message': 'Documento enviado com sucesso',
                'documento': DocumentoDetailSerializer(
                    documento, context={'request': request}
                ).data
            }
            
            response_serializer = DocumentoUploadResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        response_data = {
            'success': False,
            'message': 'Erro ao enviar documento',
            'errors': serializer.errors
        }
        
        response_serializer = DocumentoUploadResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download do documento"""
        documento = self.get_object()
        
        if not documento.arquivo:
            raise Http404("Arquivo não encontrado")
        
        # Registrar download (implementar modelo de Download se necessário)
        # Download.objects.create(documento=documento, usuario=request.user)
        
        # Determinar content type
        content_type, _ = mimetypes.guess_type(documento.arquivo.name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Preparar resposta
        response = HttpResponse(
            documento.arquivo.read(),
            content_type=content_type
        )
        
        # Definir nome do arquivo para download
        filename = f"{documento.nome}.{documento.arquivo.name.split('.')[-1]}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = documento.arquivo.size
        
        return response
    
    @action(detail=True, methods=['post'])
    def nova_versao(self, request, pk=None):
        """Criar nova versão do documento"""
        documento_original = self.get_object()
        
        serializer = NovaVersaoSerializer(
            data=request.data,
            context={
                'request': request,
                'documento_original': documento_original
            }
        )
        
        if serializer.is_valid():
            nova_versao = serializer.save()
            
            response_serializer = DocumentoDetailSerializer(
                nova_versao, context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def versoes(self, request, pk=None):
        """Listar todas as versões do documento"""
        documento = self.get_object()
        
        # Obter documento pai ou usar o próprio documento como referência
        documento_pai = documento.documento_pai or documento
        
        # Buscar todas as versões
        versoes = Documento.objects.filter(
            Q(id=documento_pai.id) | Q(documento_pai=documento_pai)
        ).order_by('-versao')
        
        serializer = DocumentoVersaoSerializer(
            versoes, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restaurar_versao(self, request, pk=None):
        """Restaurar uma versão específica como nova versão atual"""
        versao_para_restaurar = self.get_object()
        
        # Encontrar o documento principal
        documento_principal = versao_para_restaurar.documento_pai or versao_para_restaurar
        
        # Criar nova versão baseada na versão a ser restaurada
        nova_versao = Documento.objects.create(
            nome=documento_principal.nome,
            descricao=documento_principal.descricao,
            tipo=documento_principal.tipo,
            processo=documento_principal.processo,
            arquivo=versao_para_restaurar.arquivo,
            confidencial=documento_principal.confidencial,
            usuario_upload=request.user,
            versao=documento_principal.versao + 1,
            observacoes_versao=f"Restaurada da versão {versao_para_restaurar.versao}",
            hash_arquivo=versao_para_restaurar.hash_arquivo,
            documento_pai=documento_principal
        )
        
        serializer = DocumentoDetailSerializer(
            nova_versao, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def marcar_confidencial(self, request, pk=None):
        """Marcar/desmarcar documento como confidencial"""
        documento = self.get_object()
        confidencial = request.data.get('confidencial', not documento.confidencial)
        
        documento.confidencial = confidencial
        documento.save()
        
        serializer = self.get_serializer(documento)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais de documentos"""
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_documentos = queryset.count()
        documentos_confidenciais = queryset.filter(confidencial=True).count()
        
        # Documentos do mês atual
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        documentos_mes_atual = queryset.filter(data_upload__gte=inicio_mes).count()
        
        # Tamanho total
        tamanho_total = sum(
            doc.arquivo.size for doc in queryset if doc.arquivo
        )
        
        # Total de downloads (implementar se necessário)
        total_downloads = 0  # queryset.aggregate(total=Sum('downloads'))['total'] or 0
        
        # Por tipo
        por_tipo = dict(
            queryset.values('tipo').annotate(
                count=Count('id')
            ).values_list('tipo', 'count')
        )
        
        # Por extensão
        por_extensao = {}
        for doc in queryset:
            if doc.arquivo and doc.arquivo.name:
                ext = doc.arquivo.name.split('.')[-1].lower()
                por_extensao[ext] = por_extensao.get(ext, 0) + 1
        
        # Top uploaders
        top_uploaders = list(
            queryset.values(
                'usuario_upload__first_name',
                'usuario_upload__last_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
        )
        
        # Documentos mais baixados (implementar se necessário)
        mais_baixados = []
        
        data = {
            'total_documentos': total_documentos,
            'documentos_mes_atual': documentos_mes_atual,
            'tamanho_total': tamanho_total,
            'documentos_confidenciais': documentos_confidenciais,
            'total_downloads': total_downloads,
            'por_tipo': por_tipo,
            'por_extensao': por_extensao,
            'top_uploaders': top_uploaders,
            'mais_baixados': mais_baixados,
        }
        
        serializer = DocumentoStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Documentos recentes do usuário"""
        queryset = self.get_queryset()
        
        # Filtrar por usuário se não for staff
        if not request.user.is_staff:
            queryset = queryset.filter(
                Q(usuario_upload=request.user) |
                Q(processo__responsavel=request.user)
            )
        
        # Últimos 20 documentos
        documentos_recentes = queryset.order_by('-data_upload')[:20]
        
        serializer = DocumentoListSerializer(
            documentos_recentes, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def upload_multiplo(self, request):
        """Upload de múltiplos documentos"""
        arquivos = request.FILES.getlist('arquivos')
        
        if not arquivos:
            return Response(
                {'error': 'Nenhum arquivo foi enviado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resultados = []
        erros = []
        
        for arquivo in arquivos:
            # Preparar dados para cada arquivo
            data = request.data.copy()
            data['arquivo'] = arquivo
            
            # Se não foi fornecido nome, usar nome do arquivo
            if not data.get('nome'):
                data['nome'] = arquivo.name.rsplit('.', 1)[0]
            
            serializer = DocumentoCreateSerializer(
                data=data, context={'request': request}
            )
            
            if serializer.is_valid():
                documento = serializer.save()
                resultados.append({
                    'arquivo': arquivo.name,
                    'sucesso': True,
                    'documento_id': documento.id
                })
            else:
                erros.append({
                    'arquivo': arquivo.name,
                    'sucesso': False,
                    'erros': serializer.errors
                })
        
        return Response({
            'total_arquivos': len(arquivos),
            'sucessos': len(resultados),
            'erros': len(erros),
            'resultados': resultados,
            'detalhes_erros': erros
        })