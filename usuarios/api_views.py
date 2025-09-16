from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import authenticate
from datetime import timedelta

from .models import Usuario
from .serializers import (
    UsuarioSerializer, UsuarioDetailSerializer, UsuarioCreateSerializer,
    UsuarioUpdateSerializer, ChangePasswordSerializer, LoginSerializer,
    PerfilSerializer, UsuarioStatisticsSerializer, TokenResponseSerializer,
    RefreshTokenSerializer
)
from .filters import UsuarioFilter
from core.permissions import CanManageUsuarios
from core.pagination import StandardResultsSetPagination


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de usuários"""
    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated, CanManageUsuarios]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UsuarioFilter
    search_fields = ['username', 'first_name', 'last_name', 'email', 'oab_numero']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined', 'last_login']
    ordering = ['first_name', 'last_name']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Retornar serializer apropriado para cada ação"""
        if self.action == 'list':
            return UsuarioSerializer
        elif self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        return UsuarioDetailSerializer
    
    def get_queryset(self):
        """Filtrar usuários baseado nas permissões"""
        queryset = super().get_queryset()
        
        # Adicionar anotações para campos calculados
        queryset = queryset.annotate(
            total_processos=Count('processos_responsavel'),
            processos_ativos=Count(
                'processos_responsavel',
                filter=Q(processos_responsavel__status='ativo')
            ),
            prazos_pendentes=Count(
                'prazos_responsavel',
                filter=Q(prazos_responsavel__status='pendente')
            )
        )
        
        # Usuários não-staff só podem ver a si mesmos
        if not self.request.user.is_staff:
            queryset = queryset.filter(id=self.request.user.id)
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        """Endpoint de login com JWT"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Gerar tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Atualizar último login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Preparar resposta
            response_data = {
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UsuarioSerializer(user, context={'request': request}).data,
                'expires_in': access_token.payload['exp'] - access_token.payload['iat']
            }
            
            response_serializer = TokenResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def refresh_token(self, request):
        """Renovar token de acesso"""
        serializer = RefreshTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                refresh = RefreshToken(serializer.validated_data['refresh'])
                access_token = refresh.access_token
                
                response_data = {
                    'access': str(access_token),
                    'expires_in': access_token.payload['exp'] - access_token.payload['iat']
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response(
                    {'error': 'Token inválido ou expirado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout do usuário (blacklist do refresh token)"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response(
                {'message': 'Logout realizado com sucesso'},
                status=status.HTTP_200_OK
            )
        
        except Exception:
            return Response(
                {'error': 'Token inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def perfil(self, request):
        """Visualizar e editar perfil do usuário logado"""
        user = request.user
        
        if request.method == 'GET':
            # Adicionar estatísticas do usuário
            inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            user.total_processos = user.processos_responsavel.count()
            user.processos_ativos = user.processos_responsavel.filter(status='ativo').count()
            user.prazos_pendentes = user.prazos_responsavel.filter(status='pendente').count()
            user.andamentos_mes = user.andamentos.filter(created_at__gte=inicio_mes).count()
            
            serializer = PerfilSerializer(user, context={'request': request})
            return Response(serializer.data)
        
        else:  # PUT ou PATCH
            serializer = PerfilSerializer(
                user, data=request.data, partial=(request.method == 'PATCH'),
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def alterar_senha(self, request):
        """Alterar senha do usuário logado"""
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Senha alterada com sucesso'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def ativar_desativar(self, request, pk=None):
        """Ativar/desativar usuário"""
        user = self.get_object()
        ativo = request.data.get('ativo', not user.is_active)
        
        user.is_active = ativo
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resetar_senha(self, request, pk=None):
        """Resetar senha do usuário (apenas para staff)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permissão negada'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        nova_senha = request.data.get('nova_senha')
        
        if not nova_senha:
            return Response(
                {'error': 'Nova senha é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(nova_senha)
        user.save()
        
        return Response(
            {'message': 'Senha resetada com sucesso'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais de usuários"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permissão negada'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_usuarios = queryset.count()
        usuarios_ativos = queryset.filter(is_active=True).count()
        usuarios_inativos = queryset.filter(is_active=False).count()
        usuarios_staff = queryset.filter(is_staff=True).count()
        
        # Usuários do mês atual
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usuarios_mes_atual = queryset.filter(date_joined__gte=inicio_mes).count()
        
        # Por cargo
        por_cargo = dict(
            queryset.exclude(cargo__isnull=True).exclude(cargo='').values('cargo').annotate(
                count=Count('id')
            ).values_list('cargo', 'count')
        )
        
        # Por departamento
        por_departamento = dict(
            queryset.exclude(departamento__isnull=True).exclude(departamento='').values('departamento').annotate(
                count=Count('id')
            ).values_list('departamento', 'count')
        )
        
        # Usuários mais ativos (por andamentos no último mês)
        usuarios_mais_ativos = list(
            queryset.annotate(
                andamentos_mes=Count(
                    'andamentos',
                    filter=Q(andamentos__created_at__gte=inicio_mes)
                )
            ).filter(andamentos_mes__gt=0).order_by('-andamentos_mes')[:10].values(
                'id', 'first_name', 'last_name', 'andamentos_mes'
            )
        )
        
        data = {
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'usuarios_inativos': usuarios_inativos,
            'usuarios_staff': usuarios_staff,
            'usuarios_mes_atual': usuarios_mes_atual,
            'por_cargo': por_cargo,
            'por_departamento': por_departamento,
            'usuarios_mais_ativos': usuarios_mais_ativos,
        }
        
        serializer = UsuarioStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca rápida de usuários"""
        query = request.query_params.get('q', '')
        
        if len(query) < 2:
            return Response({
                'error': 'Query deve ter pelo menos 2 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(oab_numero__icontains=query)
        )[:10]  # Limitar a 10 resultados
        
        from .serializers import UsuarioResumoSerializer
        serializer = UsuarioResumoSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def online(self, request):
        """Usuários online (logados nas últimas 15 minutos)"""
        limite_online = timezone.now() - timedelta(minutes=15)
        usuarios_online = self.get_queryset().filter(
            last_login__gte=limite_online,
            is_active=True
        ).order_by('-last_login')
        
        serializer = UsuarioSerializer(usuarios_online, many=True, context={'request': request})
        return Response(serializer.data)