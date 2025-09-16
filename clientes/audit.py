"""
Sistema de auditoria para o módulo de clientes.
Registra operações importantes para rastreabilidade e conformidade.
"""

import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()

# Configuração do logger específico para auditoria
audit_logger = logging.getLogger('clientes.audit')


class AuditLog(models.Model):
    """
    Modelo para registrar logs de auditoria das operações nos clientes.
    """
    ACAO_CHOICES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('VIEW', 'Visualização'),
        ('EXPORT', 'Exportação'),
    ]
    
    # Informações da ação
    acao = models.CharField(max_length=10, choices=ACAO_CHOICES, verbose_name='Ação')
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='Data/Hora')
    
    # Usuário responsável
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuário'
    )
    usuario_nome = models.CharField(
        max_length=150, 
        blank=True,
        verbose_name='Nome do Usuário'
    )
    
    # Objeto relacionado (usando GenericForeignKey para flexibilidade)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalhes da operação
    descricao = models.TextField(verbose_name='Descrição')
    dados_anteriores = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Dados Anteriores'
    )
    dados_novos = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Dados Novos'
    )
    
    # Informações técnicas
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['acao']),
            models.Index(fields=['usuario']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_acao_display()} - {self.usuario_nome} - {self.timestamp}"


def registrar_auditoria(acao, objeto, usuario=None, request=None, dados_anteriores=None, dados_novos=None, descricao=None):
    """
    Função utilitária para registrar eventos de auditoria.
    
    Args:
        acao (str): Tipo da ação (CREATE, UPDATE, DELETE, VIEW, EXPORT)
        objeto: Objeto relacionado à ação
        usuario: Usuário que executou a ação
        request: Request HTTP (para capturar IP e User-Agent)
        dados_anteriores (dict): Estado anterior do objeto
        dados_novos (dict): Novo estado do objeto
        descricao (str): Descrição personalizada da ação
    """
    try:
        # Captura informações do usuário
        usuario_nome = ''
        if usuario:
            usuario_nome = f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username
        elif request and hasattr(request, 'user') and request.user.is_authenticated:
            usuario = request.user
            usuario_nome = f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username
        
        # Captura informações da requisição
        ip_address = None
        user_agent = ''
        if request:
            # Tenta capturar o IP real (considerando proxies)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Gera descrição automática se não fornecida
        if not descricao:
            nome_modelo = objeto.__class__.__name__
            if acao == 'CREATE':
                descricao = f"Novo {nome_modelo} criado"
            elif acao == 'UPDATE':
                descricao = f"{nome_modelo} atualizado"
            elif acao == 'DELETE':
                descricao = f"{nome_modelo} excluído"
            elif acao == 'VIEW':
                descricao = f"{nome_modelo} visualizado"
            elif acao == 'EXPORT':
                descricao = f"{nome_modelo} exportado"
            else:
                descricao = f"Ação {acao} executada em {nome_modelo}"
        
        # Cria o registro de auditoria
        content_type = ContentType.objects.get_for_model(objeto)
        
        audit_log = AuditLog.objects.create(
            acao=acao,
            usuario=usuario,
            usuario_nome=usuario_nome,
            content_type=content_type,
            object_id=str(objeto.pk),
            descricao=descricao,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log estruturado para análise
        audit_logger.info(
            f"AUDIT: {acao} | User: {usuario_nome} | Object: {content_type.model}:{objeto.pk} | IP: {ip_address}",
            extra={
                'audit_id': audit_log.id,
                'action': acao,
                'user_id': usuario.id if usuario else None,
                'user_name': usuario_nome,
                'object_type': content_type.model,
                'object_id': str(objeto.pk),
                'ip_address': ip_address,
                'timestamp': audit_log.timestamp.isoformat(),
            }
        )
        
        return audit_log
        
    except Exception as e:
        # Log do erro sem interromper o fluxo principal
        audit_logger.error(f"Erro ao registrar auditoria: {str(e)}")
        return None


def registrar_criacao_cliente(cliente, usuario=None, request=None):
    """
    Registra especificamente a criação de um novo cliente.
    """
    dados_novos = {
        'nome_razao_social': cliente.nome_razao_social,
        'tipo_pessoa': cliente.tipo_pessoa,
        'cpf_cnpj': cliente.cpf_cnpj,
        'email': cliente.email,
        'telefone': cliente.telefone,
        'status': cliente.ativo,
    }
    
    descricao = f"Novo cliente criado: {cliente.nome_razao_social} ({cliente.get_tipo_pessoa_display()})"
    
    return registrar_auditoria(
        acao='CREATE',
        objeto=cliente,
        usuario=usuario,
        request=request,
        dados_novos=dados_novos,
        descricao=descricao
    )


def registrar_atualizacao_cliente(cliente, dados_anteriores, usuario=None, request=None):
    """
    Registra a atualização de um cliente existente.
    """
    dados_novos = {
        'nome_razao_social': cliente.nome_razao_social,
        'tipo_pessoa': cliente.tipo_pessoa,
        'cpf_cnpj': cliente.cpf_cnpj,
        'email': cliente.email,
        'telefone': cliente.telefone,
        'status': cliente.ativo,
    }
    
    # Identifica campos alterados
    campos_alterados = []
    for campo, valor_novo in dados_novos.items():
        valor_anterior = dados_anteriores.get(campo)
        if valor_anterior != valor_novo:
            campos_alterados.append(campo)
    
    descricao = f"Cliente atualizado: {cliente.nome_razao_social}"
    if campos_alterados:
        descricao += f" (Campos alterados: {', '.join(campos_alterados)})"
    
    return registrar_auditoria(
        acao='UPDATE',
        objeto=cliente,
        usuario=usuario,
        request=request,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        descricao=descricao
    )


def registrar_visualizacao_cliente(cliente, usuario=None, request=None):
    """
    Registra a visualização de um cliente (para clientes sensíveis).
    """
    descricao = f"Cliente visualizado: {cliente.nome_razao_social}"
    
    return registrar_auditoria(
        acao='VIEW',
        objeto=cliente,
        usuario=usuario,
        request=request,
        descricao=descricao
    )