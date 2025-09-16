from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from typing import Optional, List

from .models import Notificacao, ConfiguracaoNotificacao, TipoNotificacao, PrioridadeNotificacao

User = get_user_model()


class NotificacaoService:
    """Serviço para gerenciamento de notificações"""
    
    @staticmethod
    def criar_notificacao(
        usuario: User,
        titulo: str,
        mensagem: str,
        tipo: str = TipoNotificacao.INFO,
        prioridade: str = PrioridadeNotificacao.MEDIA,
        url_acao: Optional[str] = None,
        icone: Optional[str] = None,
        objeto_tipo: Optional[str] = None,
        objeto_id: Optional[str] = None,
        expira_em: Optional[timezone.datetime] = None
    ) -> Notificacao:
        """Cria uma nova notificação"""
        
        # Verificar configurações do usuário
        config = NotificacaoService._get_config_usuario(usuario)
        
        # Verificar se o usuário quer receber este tipo de notificação
        if not NotificacaoService._deve_receber_notificacao(config, tipo):
            return None
        
        notificacao = Notificacao.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            prioridade=prioridade,
            url_acao=url_acao,
            icone=icone,
            objeto_tipo=objeto_tipo,
            objeto_id=objeto_id,
            expira_em=expira_em
        )
        
        return notificacao
    
    @staticmethod
    def criar_notificacao_prazo_critico(
        usuario: User,
        processo_numero: str,
        tipo_prazo: str,
        data_limite: timezone.datetime,
        processo_id: str
    ) -> Optional[Notificacao]:
        """Cria notificação para prazo crítico"""
        
        dias_restantes = (data_limite.date() - timezone.now().date()).days
        
        titulo = f"Prazo Crítico: {tipo_prazo}"
        mensagem = f"O prazo '{tipo_prazo}' do processo {processo_numero} vence em {dias_restantes} dia(s)."
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.PRAZO_CRITICO,
            prioridade=PrioridadeNotificacao.ALTA if dias_restantes <= 1 else PrioridadeNotificacao.MEDIA,
            url_acao=f"/processos/{processo_id}/",
            objeto_tipo='processo',
            objeto_id=processo_id
        )
    
    @staticmethod
    def criar_notificacao_prazo_vencido(
        usuario: User,
        processo_numero: str,
        tipo_prazo: str,
        processo_id: str
    ) -> Optional[Notificacao]:
        """Cria notificação para prazo vencido"""
        
        titulo = f"Prazo Vencido: {tipo_prazo}"
        mensagem = f"O prazo '{tipo_prazo}' do processo {processo_numero} está vencido!"
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.PRAZO_VENCIDO,
            prioridade=PrioridadeNotificacao.CRITICA,
            url_acao=f"/processos/{processo_id}/",
            objeto_tipo='processo',
            objeto_id=processo_id
        )
    
    @staticmethod
    def criar_notificacao_novo_andamento(
        usuario: User,
        processo_numero: str,
        tipo_andamento: str,
        processo_id: str
    ) -> Optional[Notificacao]:
        """Cria notificação para novo andamento"""
        
        titulo = "Novo Andamento Processual"
        mensagem = f"Novo andamento '{tipo_andamento}' adicionado ao processo {processo_numero}."
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.NOVO_ANDAMENTO,
            prioridade=PrioridadeNotificacao.MEDIA,
            url_acao=f"/processos/{processo_id}/andamentos/",
            objeto_tipo='processo',
            objeto_id=processo_id
        )
    
    @staticmethod
    def criar_notificacao_documento_upload(
        usuario: User,
        nome_documento: str,
        processo_numero: str,
        documento_id: str
    ) -> Optional[Notificacao]:
        """Cria notificação para upload de documento"""
        
        titulo = "Documento Enviado"
        mensagem = f"Documento '{nome_documento}' foi enviado para o processo {processo_numero}."
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.DOCUMENTO_UPLOAD,
            prioridade=PrioridadeNotificacao.BAIXA,
            url_acao=f"/documentos/{documento_id}/",
            objeto_tipo='documento',
            objeto_id=documento_id
        )
    
    @staticmethod
    def criar_notificacao_financeira(
        usuario: User,
        titulo: str,
        mensagem: str,
        url_acao: Optional[str] = None
    ) -> Optional[Notificacao]:
        """Cria notificação financeira"""
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.FINANCEIRO,
            prioridade=PrioridadeNotificacao.MEDIA,
            url_acao=url_acao
        )
    
    @staticmethod
    def criar_notificacao_sistema(
        usuarios: List[User],
        titulo: str,
        mensagem: str,
        prioridade: str = PrioridadeNotificacao.MEDIA,
        url_acao: Optional[str] = None
    ) -> List[Notificacao]:
        """Cria notificação do sistema para múltiplos usuários"""
        
        notificacoes = []
        
        for usuario in usuarios:
            notificacao = NotificacaoService.criar_notificacao(
                usuario=usuario,
                titulo=titulo,
                mensagem=mensagem,
                tipo=TipoNotificacao.SISTEMA,
                prioridade=prioridade,
                url_acao=url_acao
            )
            
            if notificacao:
                notificacoes.append(notificacao)
        
        return notificacoes
    
    @staticmethod
    def criar_notificacao_sucesso(
        usuario: User,
        titulo: str,
        mensagem: str,
        url_acao: Optional[str] = None
    ) -> Optional[Notificacao]:
        """Cria notificação de sucesso"""
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.SUCESSO,
            prioridade=PrioridadeNotificacao.BAIXA,
            url_acao=url_acao,
            expira_em=timezone.now() + timedelta(hours=24)  # Expira em 24h
        )
    
    @staticmethod
    def criar_notificacao_erro(
        usuario: User,
        titulo: str,
        mensagem: str,
        url_acao: Optional[str] = None
    ) -> Optional[Notificacao]:
        """Cria notificação de erro"""
        
        return NotificacaoService.criar_notificacao(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.ERRO,
            prioridade=PrioridadeNotificacao.ALTA,
            url_acao=url_acao
        )
    
    @staticmethod
    def limpar_notificacoes_expiradas():
        """Remove notificações expiradas"""
        agora = timezone.now()
        
        notificacoes_expiradas = Notificacao.objects.filter(
            expira_em__lt=agora
        )
        
        count = notificacoes_expiradas.count()
        notificacoes_expiradas.delete()
        
        return count
    
    @staticmethod
    def _get_config_usuario(usuario: User) -> ConfiguracaoNotificacao:
        """Obtém ou cria configuração do usuário"""
        config, created = ConfiguracaoNotificacao.objects.get_or_create(
            usuario=usuario
        )
        return config
    
    @staticmethod
    def _deve_receber_notificacao(config: ConfiguracaoNotificacao, tipo: str) -> bool:
        """Verifica se o usuário deve receber notificação do tipo especificado"""
        
        mapeamento_config = {
            TipoNotificacao.PRAZO_CRITICO: config.receber_prazo_critico,
            TipoNotificacao.PRAZO_VENCIDO: config.receber_prazo_critico,
            TipoNotificacao.NOVO_ANDAMENTO: config.receber_novo_andamento,
            TipoNotificacao.DOCUMENTO_UPLOAD: config.receber_documento_upload,
            TipoNotificacao.FINANCEIRO: config.receber_financeiro,
            TipoNotificacao.SISTEMA: config.receber_sistema,
        }
        
        # Para tipos não mapeados, sempre permitir
        return mapeamento_config.get(tipo, True)
    
    @staticmethod
    def verificar_prazos_criticos():
        """Verifica prazos críticos e cria notificações"""
        from processos.models import Prazo  # Import local para evitar circular
        
        # Buscar todos os usuários com configurações
        configs = ConfiguracaoNotificacao.objects.filter(
            receber_prazo_critico=True
        ).select_related('usuario')
        
        notificacoes_criadas = 0
        
        for config in configs:
            # Calcular data limite baseada na configuração do usuário
            data_limite = timezone.now().date() + timedelta(
                days=config.dias_antecedencia_prazo
            )
            
            # Buscar prazos críticos para este usuário
            prazos_criticos = Prazo.objects.filter(
                processo__usuario_responsavel=config.usuario,
                data_limite__lte=data_limite,
                data_limite__gte=timezone.now().date(),
                cumprido=False
            ).select_related('processo')
            
            for prazo in prazos_criticos:
                # Verificar se já existe notificação para este prazo
                existe_notificacao = Notificacao.objects.filter(
                    usuario=config.usuario,
                    tipo=TipoNotificacao.PRAZO_CRITICO,
                    objeto_tipo='processo',
                    objeto_id=prazo.processo.id,
                    criada_em__date=timezone.now().date()
                ).exists()
                
                if not existe_notificacao:
                    NotificacaoService.criar_notificacao_prazo_critico(
                        usuario=config.usuario,
                        processo_numero=prazo.processo.numero_processo,
                        tipo_prazo=prazo.tipo_prazo,
                        data_limite=prazo.data_limite,
                        processo_id=prazo.processo.id
                    )
                    notificacoes_criadas += 1
        
        return notificacoes_criadas