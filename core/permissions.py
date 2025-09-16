from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permissão personalizada para permitir apenas aos proprietários editar seus objetos"""
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura são permitidas para qualquer request,
        # então sempre permitimos requests GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita são apenas para o proprietário do objeto.
        # Verifica diferentes campos dependendo do modelo
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'responsavel'):
            return obj.responsavel == request.user
        elif hasattr(obj, 'usuario_upload'):
            return obj.usuario_upload == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Se não encontrar campo de proprietário, permitir apenas para staff
        return request.user.is_staff


class IsResponsavelOrReadOnly(permissions.BasePermission):
    """Permissão para processos - apenas o responsável pode editar"""
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura para todos os usuários autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita apenas para o responsável ou staff
        if hasattr(obj, 'responsavel'):
            return obj.responsavel == request.user or request.user.is_staff
        
        return request.user.is_staff


class IsClienteOwnerOrReadOnly(permissions.BasePermission):
    """Permissão para clientes - baseada em regras de negócio"""
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura para todos os usuários autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita para staff ou usuários com processos do cliente
        if request.user.is_staff:
            return True
        
        # Verificar se o usuário tem processos com este cliente
        if hasattr(obj, 'processos'):
            return obj.processos.filter(responsavel=request.user).exists()
        
        return False


class IsDocumentoOwnerOrReadOnly(permissions.BasePermission):
    """Permissão para documentos - baseada no processo e confidencialidade"""
    
    def has_object_permission(self, request, view, obj):
        # Staff tem acesso total
        if request.user.is_staff:
            return True
        
        # Verificar se o usuário é responsável pelo processo
        if obj.processo and obj.processo.responsavel == request.user:
            return True
        
        # Verificar se o usuário fez o upload
        if obj.usuario_upload == request.user:
            return True
        
        # Para documentos confidenciais, apenas proprietários
        if obj.confidencial:
            return False
        
        # Para leitura de documentos não confidenciais
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permissão que permite leitura para todos e escrita apenas para admins"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        return request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permissão que permite acesso apenas ao proprietário ou admin"""
    
    def has_object_permission(self, request, view, obj):
        # Admin tem acesso total
        if request.user.is_staff:
            return True
        
        # Verificar proprietário baseado no modelo
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'responsavel'):
            return obj.responsavel == request.user
        elif hasattr(obj, 'usuario_upload'):
            return obj.usuario_upload == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanViewFinanceiro(permissions.BasePermission):
    """Permissão para visualizar dados financeiros"""
    
    def has_permission(self, request, view):
        # Verificar se o usuário tem permissão para ver dados financeiros
        return (
            request.user.is_authenticated and (
                request.user.is_staff or
                request.user.groups.filter(name='Financeiro').exists() or
                request.user.user_permissions.filter(
                    codename='view_financeiro'
                ).exists()
            )
        )


class CanManageFinanceiro(permissions.BasePermission):
    """Permissão para gerenciar dados financeiros"""
    
    def has_permission(self, request, view):
        # Verificar se o usuário tem permissão para gerenciar dados financeiros
        return (
            request.user.is_authenticated and (
                request.user.is_staff or
                request.user.groups.filter(name='Financeiro').exists() or
                request.user.user_permissions.filter(
                    codename__in=['add_financeiro', 'change_financeiro', 'delete_financeiro']
                ).exists()
            )
        )


class CanViewRelatorios(permissions.BasePermission):
    """Permissão para visualizar relatórios"""
    
    def has_permission(self, request, view):
        # Verificar se o usuário tem permissão para ver relatórios
        return (
            request.user.is_authenticated and (
                request.user.is_staff or
                request.user.groups.filter(
                    name__in=['Relatórios', 'Gerência']
                ).exists() or
                request.user.user_permissions.filter(
                    codename='view_relatorios'
                ).exists()
            )
        )


class CanManageUsuarios(permissions.BasePermission):
    """Permissão para gerenciar usuários"""
    
    def has_permission(self, request, view):
        # Apenas staff pode gerenciar usuários
        return request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Staff pode gerenciar todos os usuários
        if request.user.is_staff:
            return True
        
        # Usuários podem editar apenas seu próprio perfil
        if request.method in ['GET', 'PUT', 'PATCH'] and obj == request.user:
            return True
        
        return False


class CanManageConfiguracoes(permissions.BasePermission):
    """Permissão para gerenciar configurações do sistema"""
    
    def has_permission(self, request, view):
        # Apenas superusuários podem gerenciar configurações
        return request.user.is_superuser