from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Alerta, StatusAlerta
from notificacoes.services import NotificacaoService
from notificacoes.models import TipoNotificacao, PrioridadeNotificacao


@receiver(post_save, sender=Alerta)
def criar_notificacao_alerta(sender, instance, created, **kwargs):
    """
    Cria uma notificação quando um alerta é criado ou atualizado
    """
    if created:
        # Criar notificação para novo alerta
        titulo = f"Novo Alerta: {instance.titulo}"
        mensagem = f"Um novo alerta foi criado para {instance.data_alerta.strftime('%d/%m/%Y às %H:%M')}."
        
        # Mapear tipo de alerta para tipo de notificação
        tipo_notificacao = _mapear_tipo_alerta_notificacao(instance.tipo)
        prioridade_notificacao = _mapear_prioridade_alerta_notificacao(instance.prioridade)
        
        NotificacaoService.criar_notificacao(
            usuario=instance.usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo_notificacao,
            prioridade=prioridade_notificacao,
            url_acao=f"/alertas/{instance.id}/",
            objeto_tipo='alerta',
            objeto_id=str(instance.id)
        )
    
    elif instance.status == StatusAlerta.CONCLUIDO:
        # Criar notificação quando alerta é concluído
        titulo = f"Alerta Concluído: {instance.titulo}"
        mensagem = f"O alerta '{instance.titulo}' foi marcado como concluído."
        
        NotificacaoService.criar_notificacao(
            usuario=instance.usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.SUCESSO,
            prioridade=PrioridadeNotificacao.BAIXA,
            url_acao=f"/alertas/{instance.id}/",
            objeto_tipo='alerta',
            objeto_id=str(instance.id)
        )


@receiver(pre_delete, sender=Alerta)
def notificar_exclusao_alerta(sender, instance, **kwargs):
    """
    Cria notificação quando um alerta é excluído
    """
    titulo = f"Alerta Excluído: {instance.titulo}"
    mensagem = f"O alerta '{instance.titulo}' foi excluído do sistema."
    
    NotificacaoService.criar_notificacao(
        usuario=instance.usuario,
        titulo=titulo,
        mensagem=mensagem,
        tipo=TipoNotificacao.AVISO,
        prioridade=PrioridadeNotificacao.BAIXA,
        objeto_tipo='alerta',
        objeto_id=str(instance.id)
    )


def _mapear_tipo_alerta_notificacao(tipo_alerta):
    """
    Mapeia tipos de alerta para tipos de notificação
    """
    mapeamento = {
        'prazo_processo': TipoNotificacao.PRAZO_CRITICO,
        'audiencia': TipoNotificacao.PROCESSO,
        'reuniao': TipoNotificacao.CLIENTE,
        'vencimento_documento': TipoNotificacao.DOCUMENTO_UPLOAD,
        'pagamento': TipoNotificacao.FINANCEIRO,
        'tarefa': TipoNotificacao.SISTEMA,
        'evento': TipoNotificacao.SISTEMA,
        'lembrete': TipoNotificacao.INFO,
        'aniversario': TipoNotificacao.CLIENTE,
        'outro': TipoNotificacao.INFO,
    }
    
    return mapeamento.get(tipo_alerta, TipoNotificacao.INFO)


def _mapear_prioridade_alerta_notificacao(prioridade_alerta):
    """
    Mapeia prioridades de alerta para prioridades de notificação
    """
    mapeamento = {
        'baixa': PrioridadeNotificacao.BAIXA,
        'media': PrioridadeNotificacao.MEDIA,
        'alta': PrioridadeNotificacao.ALTA,
        'critica': PrioridadeNotificacao.CRITICA,
    }
    
    return mapeamento.get(prioridade_alerta, PrioridadeNotificacao.MEDIA)


def processar_alertas_vencidos():
    """
    Função para processar alertas que estão próximos do vencimento
    e criar notificações apropriadas
    """
    agora = timezone.now()
    
    # Buscar alertas que devem ser disparados nos próximos 15 minutos
    alertas_proximos = Alerta.objects.filter(
        status=StatusAlerta.ATIVO,
        data_alerta__lte=agora + timedelta(minutes=15),
        data_alerta__gte=agora
    ).select_related('usuario')
    
    for alerta in alertas_proximos:
        # Verificar se já existe notificação para este alerta
        from notificacoes.models import Notificacao
        
        existe_notificacao = Notificacao.objects.filter(
            usuario=alerta.usuario,
            objeto_tipo='alerta_vencimento',
            objeto_id=str(alerta.id)
        ).exists()
        
        if not existe_notificacao:
            titulo = f"⏰ Alerta Próximo: {alerta.titulo}"
            mensagem = f"Seu alerta '{alerta.titulo}' está programado para {alerta.data_alerta.strftime('%H:%M')}."
            
            NotificacaoService.criar_notificacao(
                usuario=alerta.usuario,
                titulo=titulo,
                mensagem=mensagem,
                tipo=TipoNotificacao.AVISO,
                prioridade=_mapear_prioridade_alerta_notificacao(alerta.prioridade),
                url_acao=f"/alertas/{alerta.id}/",
                objeto_tipo='alerta_vencimento',
                objeto_id=str(alerta.id)
            )


def processar_alertas_vencidos_hoje():
    """
    Função para processar alertas que venceram hoje
    """
    hoje = timezone.now().date()
    
    # Buscar alertas que venceram hoje e ainda estão ativos
    alertas_vencidos = Alerta.objects.filter(
        status=StatusAlerta.ATIVO,
        data_vencimento__date=hoje,
        data_vencimento__lt=timezone.now()
    ).select_related('usuario')
    
    for alerta in alertas_vencidos:
        # Verificar se já existe notificação de vencimento
        from notificacoes.models import Notificacao
        
        existe_notificacao = Notificacao.objects.filter(
            usuario=alerta.usuario,
            objeto_tipo='alerta_vencido',
            objeto_id=str(alerta.id)
        ).exists()
        
        if not existe_notificacao:
            titulo = f"🚨 Alerta Vencido: {alerta.titulo}"
            mensagem = f"O alerta '{alerta.titulo}' venceu hoje e precisa de atenção."
            
            NotificacaoService.criar_notificacao(
                usuario=alerta.usuario,
                titulo=titulo,
                mensagem=mensagem,
                tipo=TipoNotificacao.PRAZO_VENCIDO,
                prioridade=PrioridadeNotificacao.ALTA,
                url_acao=f"/alertas/{alerta.id}/",
                objeto_tipo='alerta_vencido',
                objeto_id=str(alerta.id)
            )