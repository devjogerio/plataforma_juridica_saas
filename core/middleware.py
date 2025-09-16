from django.utils.deprecation import MiddlewareMixin
from usuarios.models import AuditLog
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import connection
import json
import time
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoria automática de ações dos usuários.
    Registra operações importantes para compliance e segurança.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Processa a requisição e registra informações de auditoria."""
        # Armazena informações da requisição para uso posterior
        request.audit_info = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'method': request.method,
            'path': request.path,
        }
        return None
    
    def process_response(self, request, response):
        """Processa a resposta e registra auditoria se necessário."""
        # Registra apenas para usuários autenticados
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Registra login/logout
            if request.path in ['/login/', '/logout/']:
                acao = 'login' if request.path == '/login/' and response.status_code == 302 else 'logout'
                self.create_audit_log(
                    request=request,
                    acao=acao,
                    modelo='Usuario',
                    objeto_id=str(request.user.id)
                )
            
            # Registra operações CRUD em APIs
            elif request.path.startswith('/api/') and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                acao_map = {
                    'POST': 'create',
                    'PUT': 'update',
                    'PATCH': 'update',
                    'DELETE': 'delete'
                }
                
                self.create_audit_log(
                    request=request,
                    acao=acao_map.get(request.method, 'view'),
                    modelo=self.extract_model_from_path(request.path),
                    objeto_id=self.extract_object_id_from_path(request.path)
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtém o IP real do cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def extract_model_from_path(self, path):
        """Extrai o nome do modelo a partir do caminho da URL."""
        # Remove /api/v1/ e pega o primeiro segmento
        parts = path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'api' and parts[1] == 'v1':
            return parts[2].capitalize().rstrip('s')  # Remove 's' do plural
        return 'Unknown'
    
    def extract_object_id_from_path(self, path):
        """Extrai o ID do objeto a partir do caminho da URL."""
        parts = path.strip('/').split('/')
        # Procura por UUID ou ID numérico no final do path
        for part in reversed(parts):
            if len(part) == 36 and '-' in part:  # UUID format
                return part
            elif part.isdigit():
                return part
        return None
    
    def create_audit_log(self, request, acao, modelo, objeto_id=None):
        """Cria um registro de auditoria."""
        try:
            # Prepara detalhes adicionais
            detalhes = {
                'method': request.audit_info['method'],
                'path': request.audit_info['path'],
            }
            
            # Adiciona dados do POST/PUT se disponível
            if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'body'):
                try:
                    if request.content_type == 'application/json':
                        detalhes['request_data'] = json.loads(request.body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            AuditLog.objects.create(
                usuario=request.user,
                acao=acao,
                modelo=modelo,
                objeto_id=objeto_id,
                ip_address=request.audit_info['ip_address'],
                user_agent=request.audit_info['user_agent'],
                detalhes=detalhes
            )
        except Exception as e:
            # Log do erro sem interromper a aplicação
            import logging
            logger = logging.getLogger('plataforma_juridica')
            logger.error(f"Erro ao criar log de auditoria: {e}")


class QueryCountDebugMiddleware(MiddlewareMixin):
    """
    Middleware para debug de queries em desenvolvimento
    """
    
    def process_request(self, request):
        """Inicia contagem de queries"""
        if settings.DEBUG:
            request._queries_start_count = len(connection.queries)
            request._start_time = time.time()
    
    def process_response(self, request, response):
        """Adiciona informações de performance no response"""
        if settings.DEBUG and hasattr(request, '_queries_start_count'):
            query_count = len(connection.queries) - request._queries_start_count
            response_time = time.time() - request._start_time
            
            # Log para análise
            logger.info(
                f"Path: {request.path} | "
                f"Queries: {query_count} | "
                f"Time: {response_time:.3f}s"
            )
            
            # Adiciona headers para debug
            response['X-Query-Count'] = str(query_count)
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Alerta para muitas queries
            if query_count > 20:
                logger.warning(
                    f"High query count detected: {query_count} queries for {request.path}"
                )
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware para controle de cache HTTP
    """
    
    def process_response(self, request, response):
        """Adiciona headers de cache apropriados"""
        
        # Cache para arquivos estáticos
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 ano
            return response
        
        # Cache para APIs de dados que mudam pouco
        if request.path.startswith('/api/') and request.method == 'GET':
            # Cache curto para APIs
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutos
            return response
        
        # Sem cache para páginas dinâmicas por padrão
        if not response.get('Cache-Control'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response