from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Importar ViewSets
from processos.api_views import ProcessoViewSet, AndamentoViewSet, PrazoViewSet
from clientes.api_views import ClienteViewSet
from documentos.api_views import DocumentoViewSet
from usuarios.api_views import UsuarioViewSet

# Router para ViewSets
router = DefaultRouter()

# Registrar ViewSets
router.register(r'processos', ProcessoViewSet)
router.register(r'andamentos', AndamentoViewSet)
router.register(r'prazos', PrazoViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'documentos', DocumentoViewSet)
router.register(r'usuarios', UsuarioViewSet)

# ViewSets que serão implementados posteriormente
# router.register(r'honorarios', HonorarioViewSet)
# router.register(r'despesas', DespesaViewSet)
# router.register(r'relatorios', RelatorioViewSet)

@api_view(['GET'])
def api_status(request):
    """Endpoint para verificar status da API"""
    return Response({
        'status': 'API funcionando',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'processos': '/api/processos/',
            'clientes': '/api/clientes/',
            'documentos': '/api/documentos/',
            'usuarios': '/api/usuarios/',
            'docs': '/api/docs/',
        }
    })

urlpatterns = [
    # Autenticação JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Status da API
    path('status/', api_status, name='api_status'),
    
    # Endpoints customizados
    # path('dashboard/', include('core.api_urls')),  # Dashboard geral - TODO: implementar
    # path('relatorios/', include('relatorios.api_urls')),  # Relatórios customizados - TODO: implementar
    
    # ViewSets registrados no router
    path('', include(router.urls)),
]