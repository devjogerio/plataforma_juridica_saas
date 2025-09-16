from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .models import Alerta, HistoricoAlerta, ConfiguracaoAlerta, TipoAlerta, PrioridadeAlerta, StatusAlerta
from .forms import AlertaForm, ConfiguracaoAlertaForm


class AlertaListView(LoginRequiredMixin, ListView):
    """View para listagem de alertas"""
    model = Alerta
    template_name = 'alertas/lista.html'
    context_object_name = 'alertas'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra alertas do usuário logado com filtros aplicados e otimizações"""
        queryset = Alerta.objects.filter(usuario=self.request.user).select_related('usuario')
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        prioridade = self.request.GET.get('prioridade')
        if prioridade:
            queryset = queryset.filter(prioridade=prioridade)
        
        # Filtro de período
        periodo = self.request.GET.get('periodo')
        if periodo:
            hoje = timezone.now().date()
            if periodo == 'hoje':
                queryset = queryset.filter(data_alerta__date=hoje)
            elif periodo == 'amanha':
                amanha = hoje + timedelta(days=1)
                queryset = queryset.filter(data_alerta__date=amanha)
            elif periodo == 'semana':
                fim_semana = hoje + timedelta(days=7)
                queryset = queryset.filter(data_alerta__date__range=[hoje, fim_semana])
            elif periodo == 'mes':
                fim_mes = hoje + timedelta(days=30)
                queryset = queryset.filter(data_alerta__date__range=[hoje, fim_mes])
        
        # Busca por texto
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(titulo__icontains=busca) |
                Q(descricao__icontains=busca)
            )
        
        return queryset.order_by('data_alerta', '-prioridade')
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        usuario_alertas = Alerta.objects.filter(usuario=self.request.user)
        
        context.update({
            'total_alertas': usuario_alertas.count(),
            'alertas_ativos': usuario_alertas.filter(status=StatusAlerta.ATIVO).count(),
            'alertas_hoje': usuario_alertas.filter(
                data_alerta__date=timezone.now().date(),
                status=StatusAlerta.ATIVO
            ).count(),
            'alertas_vencidos': usuario_alertas.filter(
                data_vencimento__lt=timezone.now(),
                status=StatusAlerta.ATIVO
            ).count(),
            
            # Opções para filtros
            'tipos_alerta': TipoAlerta.choices,
            'prioridades': PrioridadeAlerta.choices,
            'status_choices': StatusAlerta.choices,
            
            # Filtros ativos
            'filtro_status': self.request.GET.get('status', ''),
            'filtro_tipo': self.request.GET.get('tipo', ''),
            'filtro_prioridade': self.request.GET.get('prioridade', ''),
            'filtro_periodo': self.request.GET.get('periodo', ''),
            'filtro_busca': self.request.GET.get('busca', ''),
        })
        
        return context


class AlertaCreateView(LoginRequiredMixin, CreateView):
    """View para criação de alertas"""
    model = Alerta
    form_class = AlertaForm
    template_name = 'alertas/form.html'
    success_url = reverse_lazy('alertas:lista')
    
    def form_valid(self, form):
        """Define o usuário antes de salvar"""
        form.instance.usuario = self.request.user
        response = super().form_valid(form)
        
        # Registra no histórico
        HistoricoAlerta.objects.create(
            alerta=self.object,
            acao='criado',
            descricao='Alerta criado',
            usuario=self.request.user
        )
        
        messages.success(self.request, 'Alerta criado com sucesso!')
        return response


class AlertaUpdateView(LoginRequiredMixin, UpdateView):
    """View para edição de alertas"""
    model = Alerta
    form_class = AlertaForm
    template_name = 'alertas/form.html'
    success_url = reverse_lazy('alertas:lista')
    
    def get_queryset(self):
        """Permite editar apenas alertas do usuário logado"""
        return Alerta.objects.filter(usuario=self.request.user)
    
    def form_valid(self, form):
        """Registra a edição no histórico"""
        response = super().form_valid(form)
        
        # Registra no histórico
        HistoricoAlerta.objects.create(
            alerta=self.object,
            acao='editado',
            descricao='Alerta editado',
            usuario=self.request.user
        )
        
        messages.success(self.request, 'Alerta atualizado com sucesso!')
        return response


class AlertaDeleteView(LoginRequiredMixin, DeleteView):
    """View para exclusão de alertas"""
    model = Alerta
    template_name = 'alertas/confirmar_exclusao.html'
    success_url = reverse_lazy('alertas:lista')
    
    def get_queryset(self):
        """Permite excluir apenas alertas do usuário logado"""
        return Alerta.objects.filter(usuario=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Registra a exclusão no histórico antes de excluir"""
        self.object = self.get_object()
        
        # Registra no histórico antes de excluir
        HistoricoAlerta.objects.create(
            alerta=self.object,
            acao='cancelado',
            descricao='Alerta excluído',
            usuario=request.user
        )
        
        messages.success(request, 'Alerta excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def marcar_como_concluido(request, alerta_id):
    """Marca um alerta como concluído"""
    if request.method == 'POST':
        alerta = get_object_or_404(Alerta, id=alerta_id, usuario=request.user)
        
        if alerta.status == StatusAlerta.ATIVO:
            alerta.marcar_como_concluido()
            
            # Registra no histórico
            HistoricoAlerta.objects.create(
                alerta=alerta,
                acao='concluido',
                descricao='Alerta marcado como concluído',
                usuario=request.user
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Alerta concluído!'})
            
            messages.success(request, 'Alerta marcado como concluído!')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Alerta não pode ser concluído.'})
            
            messages.error(request, 'Alerta não pode ser concluído.')
    
    return redirect('alertas:lista')


@login_required
def adiar_alerta(request, alerta_id):
    """Adia um alerta para uma nova data"""
    if request.method == 'POST':
        alerta = get_object_or_404(Alerta, id=alerta_id, usuario=request.user)
        
        try:
            data = json.loads(request.body)
            nova_data_str = data.get('nova_data')
            
            if nova_data_str:
                nova_data = datetime.fromisoformat(nova_data_str.replace('Z', '+00:00'))
                alerta.adiar(nova_data)
                
                # Registra no histórico
                HistoricoAlerta.objects.create(
                    alerta=alerta,
                    acao='adiado',
                    descricao=f'Alerta adiado para {nova_data.strftime("%d/%m/%Y %H:%M")}',
                    usuario=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Alerta adiado para {nova_data.strftime("%d/%m/%Y %H:%M")}!'
                })
            else:
                return JsonResponse({'success': False, 'message': 'Data inválida.'})
                
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'success': False, 'message': 'Erro ao processar data.'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})


@login_required
def cancelar_alerta(request, alerta_id):
    """Cancela um alerta"""
    if request.method == 'POST':
        alerta = get_object_or_404(Alerta, id=alerta_id, usuario=request.user)
        
        if alerta.status in [StatusAlerta.ATIVO, StatusAlerta.ADIADO]:
            alerta.cancelar()
            
            # Registra no histórico
            HistoricoAlerta.objects.create(
                alerta=alerta,
                acao='cancelado',
                descricao='Alerta cancelado',
                usuario=request.user
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Alerta cancelado!'})
            
            messages.success(request, 'Alerta cancelado!')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Alerta não pode ser cancelado.'})
            
            messages.error(request, 'Alerta não pode ser cancelado.')
    
    return redirect('alertas:lista')


@login_required
def acao_lote(request):
    """Executa ações em lote nos alertas selecionados"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            acao = data.get('acao')
            alertas_ids = data.get('alertas_ids', [])
            
            if not alertas_ids:
                return JsonResponse({'success': False, 'message': 'Nenhum alerta selecionado.'})
            
            alertas = Alerta.objects.filter(
                id__in=alertas_ids,
                usuario=request.user
            )
            
            count = 0
            
            if acao == 'concluir':
                for alerta in alertas.filter(status=StatusAlerta.ATIVO):
                    alerta.marcar_como_concluido()
                    HistoricoAlerta.objects.create(
                        alerta=alerta,
                        acao='concluido',
                        descricao='Alerta concluído em lote',
                        usuario=request.user
                    )
                    count += 1
                message = f'{count} alerta(s) concluído(s)!'
                
            elif acao == 'cancelar':
                for alerta in alertas.filter(status__in=[StatusAlerta.ATIVO, StatusAlerta.ADIADO]):
                    alerta.cancelar()
                    HistoricoAlerta.objects.create(
                        alerta=alerta,
                        acao='cancelado',
                        descricao='Alerta cancelado em lote',
                        usuario=request.user
                    )
                    count += 1
                message = f'{count} alerta(s) cancelado(s)!'
                
            elif acao == 'excluir':
                # Registra no histórico antes de excluir
                for alerta in alertas:
                    HistoricoAlerta.objects.create(
                        alerta=alerta,
                        acao='cancelado',
                        descricao='Alerta excluído em lote',
                        usuario=request.user
                    )
                count = alertas.count()
                alertas.delete()
                message = f'{count} alerta(s) excluído(s)!'
            
            else:
                return JsonResponse({'success': False, 'message': 'Ação inválida.'})
            
            return JsonResponse({'success': True, 'message': message})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Erro ao processar dados.'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})


@login_required
def dashboard_alertas(request):
    """Dashboard com resumo dos alertas - otimizado para performance"""
    usuario = request.user
    hoje = timezone.now().date()
    
    # Query base otimizada
    base_queryset = Alerta.objects.filter(usuario=usuario).select_related('usuario')
    
    # Estatísticas gerais usando agregação em uma única query
    stats_queryset = base_queryset.aggregate(
        total=Count('id'),
        ativos=Count('id', filter=Q(status=StatusAlerta.ATIVO)),
        concluidos=Count('id', filter=Q(status=StatusAlerta.CONCLUIDO)),
        vencidos=Count('id', filter=Q(
            data_vencimento__lt=timezone.now(),
            status=StatusAlerta.ATIVO
        ))
    )
    
    # Alertas por período - queries otimizadas
    alertas_hoje = base_queryset.filter(
        data_alerta__date=hoje,
        status=StatusAlerta.ATIVO
    ).order_by('data_alerta')[:5]
    
    alertas_proximos = base_queryset.filter(
        data_alerta__date__gt=hoje,
        status=StatusAlerta.ATIVO
    ).order_by('data_alerta')[:10]
    
    # Alertas por tipo (últimos 30 dias) - query otimizada
    data_inicio = hoje - timedelta(days=30)
    alertas_por_tipo = base_queryset.filter(
        criado_em__date__gte=data_inicio
    ).values('tipo').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Alertas por prioridade - query otimizada
    alertas_por_prioridade = base_queryset.filter(
        status=StatusAlerta.ATIVO
    ).values('prioridade').annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'stats': stats_queryset,
        'alertas_hoje': alertas_hoje,
        'alertas_proximos': alertas_proximos,
        'alertas_por_tipo': alertas_por_tipo,
        'alertas_por_prioridade': alertas_por_prioridade,
    }
    
    return render(request, 'alertas/dashboard.html', context)


class ConfiguracaoAlertaUpdateView(LoginRequiredMixin, UpdateView):
    """View para configurações de alertas do usuário"""
    model = ConfiguracaoAlerta
    form_class = ConfiguracaoAlertaForm
    template_name = 'alertas/configuracoes.html'
    success_url = reverse_lazy('alertas:configuracoes')
    
    def get_object(self, queryset=None):
        """Obtém ou cria a configuração do usuário"""
        obj, created = ConfiguracaoAlerta.objects.get_or_create(
            usuario=self.request.user
        )
        return obj
    
    def form_valid(self, form):
        """Salva as configurações"""
        response = super().form_valid(form)
        messages.success(self.request, 'Configurações salvas com sucesso!')
        return response


@login_required
def api_alertas_proximos(request):
    """API para obter alertas próximos (para widgets) - otimizada"""
    limite = int(request.GET.get('limite', 5))
    
    # Query otimizada com select_related
    alertas = Alerta.objects.filter(
        usuario=request.user,
        status=StatusAlerta.ATIVO,
        data_alerta__gte=timezone.now()
    ).select_related('usuario').order_by('data_alerta')[:limite]
    
    data = []
    for alerta in alertas:
        data.append({
            'id': str(alerta.id),
            'titulo': alerta.titulo,
            'tipo': alerta.get_tipo_display(),
            'prioridade': alerta.get_prioridade_display(),
            'data_alerta': alerta.data_alerta.isoformat(),
            'icone': alerta.get_icone_classe(),
            'cor': alerta.get_cor_prioridade(),
            'url_acao': alerta.url_acao or '',
        })
    
    return JsonResponse({'alertas': data})