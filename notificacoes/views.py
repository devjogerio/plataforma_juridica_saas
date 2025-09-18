from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_http_methods

from .models import Notificacao, ConfiguracaoNotificacao, TipoNotificacao, PrioridadeNotificacao
from .services import NotificacaoService


class NotificacaoListView(LoginRequiredMixin, ListView):
    """Lista de notificações do usuário"""
    model = Notificacao
    template_name = 'notificacoes/lista.html'
    context_object_name = 'notificacoes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Notificacao.objects.filter(
            usuario=self.request.user
        ).select_related('usuario')
        
        # Filtros
        tipo = self.request.GET.get('tipo')
        if tipo and tipo in [choice[0] for choice in TipoNotificacao.choices]:
            queryset = queryset.filter(tipo=tipo)
        
        lida = self.request.GET.get('lida')
        if lida == 'true':
            queryset = queryset.filter(lida=True)
        elif lida == 'false':
            queryset = queryset.filter(lida=False)
        
        prioridade = self.request.GET.get('prioridade')
        if prioridade and prioridade in [choice[0] for choice in PrioridadeNotificacao.choices]:
            queryset = queryset.filter(prioridade=prioridade)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        usuario_notificacoes = Notificacao.objects.filter(usuario=self.request.user)
        
        context['total_notificacoes'] = usuario_notificacoes.count()
        context['nao_lidas'] = usuario_notificacoes.filter(lida=False).count()
        context['hoje'] = usuario_notificacoes.filter(
            criada_em__date=timezone.now().date()
        ).count()
        context['urgentes'] = usuario_notificacoes.filter(
            prioridade='alta', lida=False
        ).count()
        
        # Opções de filtro
        context['tipos_notificacao'] = TipoNotificacao.choices
        context['prioridades'] = PrioridadeNotificacao.choices
        
        return context


@login_required
def marcar_como_lida(request, notificacao_id):
    """Marca uma notificação como lida"""
    if request.method == 'POST':
        notificacao = get_object_or_404(
            Notificacao, 
            id=notificacao_id, 
            usuario=request.user
        )
        
        notificacao.marcar_como_lida()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Notificação marcada como lida'
            })
        
        messages.success(request, 'Notificação marcada como lida.')
        
        # Redirecionar para URL de ação se existir
        if notificacao.url_acao:
            return redirect(notificacao.url_acao)
        
        return redirect('notificacoes:lista')
    
    return redirect('notificacoes:lista')


@login_required
def marcar_como_nao_lida(request, notificacao_id):
    """Marca uma notificação como não lida"""
    if request.method == 'POST':
        notificacao = get_object_or_404(
            Notificacao, 
            id=notificacao_id, 
            usuario=request.user
        )
        
        notificacao.lida = False
        notificacao.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
@require_http_methods(["POST"])
def marcar_todas_como_lidas(request):
    """
    Marca todas as notificações do usuário como lidas
    """
    notificacoes = Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    )
    
    count = notificacoes.count()
    notificacoes.update(lida=True, data_leitura=timezone.now())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{count} notificações marcadas como lidas',
            'count': count
        })
    
    messages.success(request, f'{count} notificações marcadas como lidas')
    return redirect('notificacoes:lista')


@login_required
@require_http_methods(["POST"])
def excluir_notificacao(request, notificacao_id):
    """
    Exclui uma notificação específica
    """
    notificacao = get_object_or_404(
        Notificacao,
        id=notificacao_id,
        usuario=request.user
    )
    
    notificacao.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Notificação excluída com sucesso'
        })
    
    messages.success(request, 'Notificação excluída com sucesso')
    return redirect('notificacoes:lista')


@login_required
@require_http_methods(["POST"])
def excluir_multiplas_notificacoes(request):
    """
    Exclui múltiplas notificações
    """
    notificacao_ids = request.POST.getlist('notificacao_ids')
    
    if not notificacao_ids:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma notificação selecionada'
            })
        messages.error(request, 'Nenhuma notificação selecionada')
        return redirect('notificacoes:lista')
    
    count = Notificacao.objects.filter(
        id__in=notificacao_ids,
        usuario=request.user
    ).delete()[0]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{count} notificações excluídas com sucesso',
            'count': count
        })
    
    messages.success(request, f'{count} notificações excluídas com sucesso')
    return redirect('notificacoes:lista')


@login_required
@require_http_methods(["POST"])
def limpar_lidas(request):
    """
    Remove todas as notificações lidas do usuário
    """
    count = Notificacao.objects.filter(
        usuario=request.user,
        lida=True
    ).delete()[0]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{count} notificações lidas removidas',
            'count': count
        })
    
    messages.success(request, f'{count} notificações lidas removidas')
    return redirect('notificacoes:lista')


@login_required
@require_http_methods(["GET"])
def notificacoes_recentes_ajax(request):
    """
    Retorna notificações recentes via AJAX
    """
    try:
        notificacoes = Notificacao.objects.filter(
            usuario=request.user
        ).select_related('usuario').order_by('-criada_em')[:10]
        
        data = []
        for notificacao in notificacoes:
            data.append({
                'id': notificacao.id,
                'titulo': notificacao.titulo,
                'mensagem': notificacao.mensagem,
                'tipo': notificacao.tipo,
                'lida': notificacao.lida,
                'data_criacao': notificacao.criada_em.isoformat(),
                'url_acao': notificacao.url_acao or '#',
                'icone': notificacao.get_icone_classe(),
                'cor': notificacao.get_cor_classe()
            })
        
        return JsonResponse({
            'notificacoes': data,
            'total_nao_lidas': notificacoes.filter(lida=False).count()
        })
    except Exception as e:
        # Log do erro para debug
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao carregar notificações para usuário {request.user.id}: {str(e)}")
        
        # Retornar resposta vazia em caso de erro
        return JsonResponse({
            'notificacoes': [],
            'total_nao_lidas': 0
        })


@login_required
def dashboard_notificacoes(request):
    """Dashboard de notificações"""
    # Estatísticas gerais
    total_notificacoes = Notificacao.objects.filter(usuario=request.user).count()
    nao_lidas = Notificacao.objects.filter(usuario=request.user, lida=False).count()
    
    # Notificações por tipo (últimos 30 dias)
    data_limite = timezone.now() - timedelta(days=30)
    notificacoes_por_tipo = {}
    
    for tipo_choice in TipoNotificacao.choices:
        tipo_code = tipo_choice[0]
        count = Notificacao.objects.filter(
            usuario=request.user,
            tipo=tipo_code,
            criada_em__gte=data_limite
        ).count()
        notificacoes_por_tipo[tipo_choice[1]] = count
    
    # Notificações críticas não lidas
    criticas = Notificacao.objects.filter(
        usuario=request.user,
        prioridade=PrioridadeNotificacao.CRITICA,
        lida=False
    ).order_by('-criada_em')[:5]
    
    # Notificações recentes
    recentes = Notificacao.objects.filter(
        usuario=request.user
    ).order_by('-criada_em')[:10]
    
    context = {
        'total_notificacoes': total_notificacoes,
        'nao_lidas': nao_lidas,
        'notificacoes_por_tipo': notificacoes_por_tipo,
        'criticas': criticas,
        'recentes': recentes,
    }
    
    return render(request, 'notificacoes/dashboard.html', context)


class ConfiguracaoNotificacaoUpdateView(LoginRequiredMixin, UpdateView):
    """Configurações de notificação do usuário"""
    model = ConfiguracaoNotificacao
    template_name = 'notificacoes/configuracoes.html'
    fields = [
        'receber_prazo_critico',
        'receber_novo_andamento', 
        'receber_documento_upload',
        'receber_financeiro',
        'receber_sistema',
        'notificacao_email',
        'dias_antecedencia_prazo'
    ]
    success_url = reverse_lazy('notificacoes:configuracoes')
    
    def get_object(self, queryset=None):
        """Obtém ou cria a configuração do usuário"""
        config, created = ConfiguracaoNotificacao.objects.get_or_create(
            usuario=self.request.user
        )
        return config
    
    def form_valid(self, form):
        messages.success(self.request, 'Configurações de notificação atualizadas.')
        return super().form_valid(form)


def _tempo_relativo(data):
    """Calcula tempo relativo de uma data"""
    agora = timezone.now()
    diferenca = agora - data
    
    if diferenca.days > 0:
        return f'{diferenca.days} dia{"s" if diferenca.days > 1 else ""} atrás'
    elif diferenca.seconds > 3600:
        horas = diferenca.seconds // 3600
        return f'{horas} hora{"s" if horas > 1 else ""} atrás'
    elif diferenca.seconds > 60:
        minutos = diferenca.seconds // 60
        return f'{minutos} minuto{"s" if minutos > 1 else ""} atrás'
    else:
        return 'Agora mesmo'
