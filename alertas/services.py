from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Optional, List, Dict, Any

from .models import Alerta, ConfiguracaoAlerta, TipoAlerta, PrioridadeAlerta, StatusAlerta
from notificacoes.services import NotificacaoService
from notificacoes.models import TipoNotificacao, PrioridadeNotificacao

User = get_user_model()


class AlertaService:
    """Serviço para gerenciamento de alertas e lembretes"""
    
    @staticmethod
    def criar_alerta(
        usuario: User,
        titulo: str,
        descricao: str = "",
        tipo: str = TipoAlerta.LEMBRETE,
        prioridade: str = PrioridadeAlerta.MEDIA,
        data_alerta: datetime = None,
        data_vencimento: datetime = None,
        antecedencia_minutos: int = None,
        recorrente: bool = False,
        frequencia_recorrencia: str = None,
        notificar_email: bool = False,
        url_acao: str = None
    ) -> Alerta:
        """Cria um novo alerta"""
        
        # Verificar configurações do usuário
        config = AlertaService._get_config_usuario(usuario)
        
        # Verificar se o usuário quer receber este tipo de alerta
        if not AlertaService._deve_receber_alerta(config, tipo):
            return None
        
        # Usar antecedência padrão se não especificada
        if antecedencia_minutos is None:
            antecedencia_minutos = config.antecedencia_padrao
        
        alerta = Alerta.objects.create(
            usuario=usuario,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            prioridade=prioridade,
            data_alerta=data_alerta or timezone.now(),
            data_vencimento=data_vencimento,
            antecedencia_minutos=antecedencia_minutos,
            recorrente=recorrente,
            frequencia_recorrencia=frequencia_recorrencia,
            notificar_email=notificar_email,
            url_acao=url_acao
        )
        
        return alerta
    
    @staticmethod
    def criar_alerta_prazo_processo(
        usuario: User,
        processo_numero: str,
        tipo_prazo: str,
        data_limite: datetime,
        processo_id: int,
        dias_antecedencia: int = 3
    ) -> Optional[Alerta]:
        """Cria alerta para prazo processual"""
        
        data_alerta = data_limite - timedelta(days=dias_antecedencia)
        
        titulo = f"Prazo Processual: {tipo_prazo}"
        descricao = f"Prazo '{tipo_prazo}' do processo {processo_numero} vence em {data_limite.strftime('%d/%m/%Y')}."
        
        return AlertaService.criar_alerta(
            usuario=usuario,
            titulo=titulo,
            descricao=descricao,
            tipo=TipoAlerta.PRAZO_PROCESSO,
            prioridade=PrioridadeAlerta.ALTA,
            data_alerta=data_alerta,
            data_vencimento=data_limite,
            url_acao=f"/processos/{processo_id}/prazos/"
        )
    
    @staticmethod
    def criar_alerta_audiencia(
        usuario: User,
        processo_numero: str,
        data_audiencia: datetime,
        tipo_audiencia: str,
        processo_id: int,
        horas_antecedencia: int = 2
    ) -> Optional[Alerta]:
        """Cria alerta para audiência"""
        
        data_alerta = data_audiencia - timedelta(hours=horas_antecedencia)
        
        titulo = f"Audiência: {tipo_audiencia}"
        descricao = f"Audiência de {tipo_audiencia} do processo {processo_numero} às {data_audiencia.strftime('%H:%M')}."
        
        return AlertaService.criar_alerta(
            usuario=usuario,
            titulo=titulo,
            descricao=descricao,
            tipo=TipoAlerta.AUDIENCIA,
            prioridade=PrioridadeAlerta.CRITICA,
            data_alerta=data_alerta,
            data_vencimento=data_audiencia,
            url_acao=f"/processos/{processo_id}/audiencias/"
        )
    
    @staticmethod
    def criar_alerta_reuniao(
        usuario: User,
        cliente_nome: str,
        data_reuniao: datetime,
        assunto: str,
        cliente_id: int,
        minutos_antecedencia: int = 30
    ) -> Optional[Alerta]:
        """Cria alerta para reunião com cliente"""
        
        data_alerta = data_reuniao - timedelta(minutes=minutos_antecedencia)
        
        titulo = f"Reunião: {cliente_nome}"
        descricao = f"Reunião com {cliente_nome} sobre {assunto} às {data_reuniao.strftime('%H:%M')}."
        
        return AlertaService.criar_alerta(
            usuario=usuario,
            titulo=titulo,
            descricao=descricao,
            tipo=TipoAlerta.REUNIAO,
            prioridade=PrioridadeAlerta.MEDIA,
            data_alerta=data_alerta,
            data_vencimento=data_reuniao,
            url_acao=f"/clientes/{cliente_id}/"
        )
    
    @staticmethod
    def criar_alerta_pagamento(
        usuario: User,
        descricao_pagamento: str,
        data_vencimento: datetime,
        valor: float,
        dias_antecedencia: int = 5
    ) -> Optional[Alerta]:
        """Cria alerta para pagamento"""
        
        data_alerta = data_vencimento - timedelta(days=dias_antecedencia)
        
        titulo = f"Pagamento: R$ {valor:,.2f}"
        descricao_completa = f"Pagamento de {descricao_pagamento} no valor de R$ {valor:,.2f} vence em {data_vencimento.strftime('%d/%m/%Y')}."
        
        return AlertaService.criar_alerta(
            usuario=usuario,
            titulo=titulo,
            descricao=descricao_completa,
            tipo=TipoAlerta.PAGAMENTO,
            prioridade=PrioridadeAlerta.ALTA,
            data_alerta=data_alerta,
            data_vencimento=data_vencimento,
            url_acao="/financeiro/"
        )
    
    @staticmethod
    def marcar_como_concluido(alerta_id: str, usuario: User) -> bool:
        """Marca um alerta como concluído"""
        try:
            alerta = Alerta.objects.get(id=alerta_id, usuario=usuario)
            alerta.status = StatusAlerta.CONCLUIDO
            alerta.concluido_em = timezone.now()
            alerta.save()
            
            # Criar notificação de conclusão
            NotificacaoService.criar_notificacao(
                usuario=usuario,
                titulo=f"✅ Alerta Concluído",
                mensagem=f"O alerta '{alerta.titulo}' foi marcado como concluído.",
                tipo=TipoNotificacao.SUCESSO,
                prioridade=PrioridadeNotificacao.BAIXA
            )
            
            return True
        except Alerta.DoesNotExist:
            return False
    
    @staticmethod
    def adiar_alerta(alerta_id: str, usuario: User, nova_data: datetime) -> bool:
        """Adia um alerta para uma nova data"""
        try:
            alerta = Alerta.objects.get(id=alerta_id, usuario=usuario)
            data_anterior = alerta.data_alerta
            
            alerta.data_alerta = nova_data
            alerta.status = StatusAlerta.ADIADO
            alerta.save()
            
            # Criar notificação de adiamento
            NotificacaoService.criar_notificacao(
                usuario=usuario,
                titulo=f"📅 Alerta Adiado",
                mensagem=f"O alerta '{alerta.titulo}' foi adiado de {data_anterior.strftime('%d/%m/%Y %H:%M')} para {nova_data.strftime('%d/%m/%Y %H:%M')}.",
                tipo=TipoNotificacao.AVISO,
                prioridade=PrioridadeNotificacao.MEDIA
            )
            
            return True
        except Alerta.DoesNotExist:
            return False
    
    @staticmethod
    def cancelar_alerta(alerta_id: str, usuario: User) -> bool:
        """Cancela um alerta"""
        try:
            alerta = Alerta.objects.get(id=alerta_id, usuario=usuario)
            alerta.status = StatusAlerta.CANCELADO
            alerta.save()
            
            # Criar notificação de cancelamento
            NotificacaoService.criar_notificacao(
                usuario=usuario,
                titulo=f"❌ Alerta Cancelado",
                mensagem=f"O alerta '{alerta.titulo}' foi cancelado.",
                tipo=TipoNotificacao.AVISO,
                prioridade=PrioridadeNotificacao.BAIXA
            )
            
            return True
        except Alerta.DoesNotExist:
            return False
    
    @staticmethod
    def obter_alertas_proximos(usuario: User, limite: int = 10) -> List[Alerta]:
        """Obtém alertas próximos do usuário"""
        return Alerta.objects.filter(
            usuario=usuario,
            status=StatusAlerta.ATIVO,
            data_alerta__gte=timezone.now()
        ).order_by('data_alerta')[:limite]
    
    @staticmethod
    def obter_alertas_hoje(usuario: User) -> List[Alerta]:
        """Obtém alertas de hoje do usuário"""
        hoje = timezone.now().date()
        return Alerta.objects.filter(
            usuario=usuario,
            status=StatusAlerta.ATIVO,
            data_alerta__date=hoje
        ).order_by('data_alerta')
    
    @staticmethod
    def obter_alertas_vencidos(usuario: User) -> List[Alerta]:
        """Obtém alertas vencidos do usuário"""
        return Alerta.objects.filter(
            usuario=usuario,
            status=StatusAlerta.ATIVO,
            data_vencimento__lt=timezone.now()
        ).order_by('data_vencimento')
    
    @staticmethod
    def obter_estatisticas_alertas(usuario: User) -> Dict[str, Any]:
        """Obtém estatísticas dos alertas do usuário"""
        alertas = Alerta.objects.filter(usuario=usuario)
        
        return {
            'total': alertas.count(),
            'ativos': alertas.filter(status=StatusAlerta.ATIVO).count(),
            'concluidos': alertas.filter(status=StatusAlerta.CONCLUIDO).count(),
            'cancelados': alertas.filter(status=StatusAlerta.CANCELADO).count(),
            'vencidos': alertas.filter(
                status=StatusAlerta.ATIVO,
                data_vencimento__lt=timezone.now()
            ).count(),
            'hoje': alertas.filter(
                status=StatusAlerta.ATIVO,
                data_alerta__date=timezone.now().date()
            ).count(),
        }
    
    @staticmethod
    def processar_alertas_recorrentes():
        """Processa alertas recorrentes e cria novas instâncias"""
        alertas_recorrentes = Alerta.objects.filter(
            recorrente=True,
            status=StatusAlerta.ATIVO,
            data_alerta__lt=timezone.now()
        )
        
        alertas_criados = 0
        
        for alerta in alertas_recorrentes:
            # Calcular próxima data baseada na frequência
            proxima_data = AlertaService._calcular_proxima_data_recorrencia(
                alerta.data_alerta, 
                alerta.frequencia_recorrencia
            )
            
            if proxima_data:
                # Criar novo alerta
                novo_alerta = Alerta.objects.create(
                    usuario=alerta.usuario,
                    titulo=alerta.titulo,
                    descricao=alerta.descricao,
                    tipo=alerta.tipo,
                    prioridade=alerta.prioridade,
                    data_alerta=proxima_data,
                    data_vencimento=alerta.data_vencimento,
                    antecedencia_minutos=alerta.antecedencia_minutos,
                    recorrente=True,
                    frequencia_recorrencia=alerta.frequencia_recorrencia,
                    notificar_email=alerta.notificar_email,
                    url_acao=alerta.url_acao
                )
                
                alertas_criados += 1
                
                # Marcar alerta anterior como concluído
                alerta.status = StatusAlerta.CONCLUIDO
                alerta.concluido_em = timezone.now()
                alerta.save()
        
        return alertas_criados
    
    @staticmethod
    def _get_config_usuario(usuario: User) -> ConfiguracaoAlerta:
        """Obtém ou cria configuração do usuário"""
        config, created = ConfiguracaoAlerta.objects.get_or_create(
            usuario=usuario
        )
        return config
    
    @staticmethod
    def _deve_receber_alerta(config: ConfiguracaoAlerta, tipo: str) -> bool:
        """Verifica se o usuário deve receber alerta do tipo especificado"""
        
        if not config.alertas_ativos:
            return False
        
        mapeamento_config = {
            TipoAlerta.PRAZO_PROCESSO: config.alertas_prazos,
            TipoAlerta.AUDIENCIA: config.alertas_audiencias,
            TipoAlerta.REUNIAO: config.alertas_reunioes,
            TipoAlerta.PAGAMENTO: config.alertas_pagamentos,
            TipoAlerta.TAREFA: config.alertas_tarefas,
        }
        
        # Para tipos não mapeados, sempre permitir
        return mapeamento_config.get(tipo, True)
    
    @staticmethod
    def _calcular_proxima_data_recorrencia(data_atual: datetime, frequencia: str) -> Optional[datetime]:
        """Calcula a próxima data para alertas recorrentes"""
        
        if frequencia == 'diario':
            return data_atual + timedelta(days=1)
        elif frequencia == 'semanal':
            return data_atual + timedelta(weeks=1)
        elif frequencia == 'mensal':
            # Adicionar um mês (aproximadamente)
            return data_atual + timedelta(days=30)
        elif frequencia == 'anual':
            return data_atual + timedelta(days=365)
        
        return None