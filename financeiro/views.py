from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import chain
from operator import attrgetter
import json

from .models import Honorario, ParcelaHonorario, Despesa, ContaBancaria
from .forms import HonorarioForm, ParcelaHonorarioForm, DespesaForm, ContaBancariaForm, FiltroFinanceiroForm
from processos.models import Processo
from clientes.models import Cliente


class FinanceiroDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard principal do módulo financeiro com KPIs e gráficos
    """
    template_name = 'financeiro/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtrar dados por usuário se não for staff
        if self.request.user.is_staff:
            honorarios_qs = Honorario.objects.all()
            despesas_qs = Despesa.objects.all()
        else:
            honorarios_qs = Honorario.objects.filter(
                processo__responsavel=self.request.user
            )
            despesas_qs = Despesa.objects.filter(
                processo__responsavel=self.request.user
            )
        
        # KPIs principais
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Honorários
        total_honorarios = honorarios_qs.aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        honorarios_recebidos = honorarios_qs.filter(
            status_pagamento='pago'
        ).aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        honorarios_pendentes = honorarios_qs.filter(
            status_pagamento__in=['pendente', 'parcial']
        ).aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        honorarios_vencidos = honorarios_qs.filter(
            data_vencimento__lt=hoje,
            status_pagamento__in=['pendente', 'parcial']
        ).count()
        
        # Despesas
        total_despesas = despesas_qs.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        despesas_mes = despesas_qs.filter(
            data_despesa__gte=inicio_mes
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        # Honorários por mês (últimos 12 meses)
        honorarios_por_mes = []
        for i in range(12):
            mes = hoje - timedelta(days=30*i)
            inicio_mes_calc = mes.replace(day=1)
            if mes.month == 12:
                fim_mes = mes.replace(year=mes.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fim_mes = mes.replace(month=mes.month+1, day=1) - timedelta(days=1)
            
            valor = honorarios_qs.filter(
                data_vencimento__gte=inicio_mes_calc,
                data_vencimento__lte=fim_mes,
                status_pagamento='pago'
            ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
            
            honorarios_por_mes.append({
                'mes': mes.strftime('%m/%Y'),
                'valor': float(valor)
            })
        
        honorarios_por_mes.reverse()
        
        # Próximos vencimentos
        proximos_vencimentos = honorarios_qs.filter(
            data_vencimento__gte=hoje,
            data_vencimento__lte=hoje + timedelta(days=30),
            status_pagamento__in=['pendente', 'parcial']
        ).select_related('processo', 'cliente').order_by('data_vencimento')[:10]
        
        context.update({
            'total_honorarios': total_honorarios,
            'honorarios_recebidos': honorarios_recebidos,
            'honorarios_pendentes': honorarios_pendentes,
            'honorarios_vencidos': honorarios_vencidos,
            'total_despesas': total_despesas,
            'despesas_mes': despesas_mes,
            'honorarios_por_mes': json.dumps(honorarios_por_mes),
            'proximos_vencimentos': proximos_vencimentos,
        })
        
        return context


class HonorarioListView(LoginRequiredMixin, ListView):
    """
    Listagem de honorários com filtros e paginação
    """
    model = Honorario
    template_name = 'financeiro/honorarios.html'
    context_object_name = 'honorarios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Honorario.objects.select_related(
            'processo', 'cliente', 'processo__tipo_processo'
        )
        
        # Filtrar por usuário se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        
        # Filtros de busca
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(processo__numero_processo__icontains=q) |
                Q(cliente__nome_razao_social__icontains=q) |
                Q(observacoes__icontains=q)
            )
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status_pagamento=status)
        
        # Filtro por tipo de cobrança
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_cobranca=tipo)
        
        # Filtro por período
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data_vencimento__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_vencimento__lte=data_fim)
        
        return queryset.order_by('-data_vencimento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        base_queryset = self.get_queryset()
        context.update({
            'total_honorarios': base_queryset.count(),
            'valor_total': base_queryset.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00'),
            'honorarios_pendentes': base_queryset.filter(status_pagamento='pendente').count(),
            'honorarios_vencidos': base_queryset.filter(
                data_vencimento__lt=date.today(),
                status_pagamento__in=['pendente', 'parcial']
            ).count(),
        })
        
        return context


class HonorarioDetailView(LoginRequiredMixin, DetailView):
    model = Honorario
    template_name = 'financeiro/honorario_detalhe.html'
    login_url = '/login/'


class HonorarioCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de novo honorário
    """
    model = Honorario
    form_class = HonorarioForm
    template_name = 'financeiro/honorario_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Honorário cadastrado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financeiro:detalhe_honorario', kwargs={'pk': self.object.pk})


class HonorarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edição de honorário existente
    """
    model = Honorario
    form_class = HonorarioForm
    template_name = 'financeiro/honorario_form.html'
    
    def get_queryset(self):
        queryset = Honorario.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        return queryset
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Honorário atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financeiro:detalhe_honorario', kwargs={'pk': self.object.pk})


class DespesaListView(LoginRequiredMixin, ListView):
    """
    Listagem de despesas com filtros e paginação
    """
    model = Despesa
    template_name = 'financeiro/despesas.html'
    context_object_name = 'despesas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Despesa.objects.select_related(
            'processo', 'processo__cliente', 'usuario_lancamento'
        )
        
        # Filtrar por usuário se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        
        # Filtros de busca
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(processo__numero_processo__icontains=q) |
                Q(descricao__icontains=q) |
                Q(fornecedor__icontains=q)
            )
        
        # Filtro por tipo de despesa
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_despesa=tipo)
        
        # Filtro por status de reembolso
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status_reembolso=status)
        
        # Filtro por período
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data_despesa__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_despesa__lte=data_fim)
        
        return queryset.order_by('-data_despesa')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        base_queryset = self.get_queryset()
        context.update({
            'total_despesas': base_queryset.count(),
            'valor_total': base_queryset.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00'),
            'despesas_pendentes': base_queryset.filter(status_reembolso='pendente').count(),
            'despesas_reembolsadas': base_queryset.filter(status_reembolso='reembolsado').count(),
        })
        
        return context


class DespesaDetailView(LoginRequiredMixin, DetailView):
    model = Despesa
    template_name = 'financeiro/despesa_detalhe.html'
    login_url = '/login/'


class DespesaCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de nova despesa
    """
    model = Despesa
    form_class = DespesaForm
    template_name = 'financeiro/despesa_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.usuario_lancamento = self.request.user
        messages.success(self.request, 'Despesa cadastrada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financeiro:detalhe_despesa', kwargs={'pk': self.object.pk})


class DespesaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edição de despesa existente
    """
    model = Despesa
    form_class = DespesaForm
    template_name = 'financeiro/despesa_form.html'
    
    def get_queryset(self):
        queryset = Despesa.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(processo__responsavel=self.request.user)
        return queryset
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Despesa atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financeiro:detalhe_despesa', kwargs={'pk': self.object.pk})


class RelatoriosFinanceirosView(LoginRequiredMixin, TemplateView):
    """
    Relatórios financeiros com filtros e exportação
    """
    template_name = 'financeiro/relatorios.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulário de filtros
        form = FiltroFinanceiroForm(self.request.GET, user=self.request.user)
        context['form'] = form
        
        if form.is_valid():
            # Aplicar filtros
            data_inicio, data_fim = self._get_periodo_filtro(form.cleaned_data)
            
            # Filtrar dados por usuário se não for staff
            if self.request.user.is_staff:
                honorarios_qs = Honorario.objects.all()
                despesas_qs = Despesa.objects.all()
            else:
                honorarios_qs = Honorario.objects.filter(
                    processo__responsavel=self.request.user
                )
                despesas_qs = Despesa.objects.filter(
                    processo__responsavel=self.request.user
                )
            
            # Aplicar filtros de período
            if data_inicio:
                honorarios_qs = honorarios_qs.filter(data_vencimento__gte=data_inicio)
                despesas_qs = despesas_qs.filter(data_despesa__gte=data_inicio)
            if data_fim:
                honorarios_qs = honorarios_qs.filter(data_vencimento__lte=data_fim)
                despesas_qs = despesas_qs.filter(data_despesa__lte=data_fim)
            
            # Filtros adicionais
            processo = form.cleaned_data.get('processo')
            if processo:
                honorarios_qs = honorarios_qs.filter(processo=processo)
                despesas_qs = despesas_qs.filter(processo=processo)
            
            cliente = form.cleaned_data.get('cliente')
            if cliente:
                honorarios_qs = honorarios_qs.filter(cliente=cliente)
                despesas_qs = despesas_qs.filter(processo__cliente=cliente)
            
            # Calcular totais
            context.update({
                'honorarios_total': honorarios_qs.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00'),
                'honorarios_recebidos': honorarios_qs.filter(status_pagamento='pago').aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00'),
                'honorarios_pendentes': honorarios_qs.filter(status_pagamento__in=['pendente', 'parcial']).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00'),
                'despesas_total': despesas_qs.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00'),
                'despesas_reembolsadas': despesas_qs.filter(status_reembolso='reembolsado').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00'),
                'despesas_pendentes': despesas_qs.filter(status_reembolso='pendente').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00'),
                'honorarios': honorarios_qs.select_related('processo', 'cliente')[:50],
                'despesas': despesas_qs.select_related('processo', 'processo__cliente')[:50],
            })
        
        return context
    
    def _get_periodo_filtro(self, cleaned_data):
        """
        Converte o período selecionado em datas de início e fim
        """
        periodo = cleaned_data.get('periodo')
        hoje = date.today()
        
        if periodo == 'hoje':
            return hoje, hoje
        elif periodo == 'ontem':
            ontem = hoje - timedelta(days=1)
            return ontem, ontem
        elif periodo == 'esta_semana':
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            return inicio_semana, hoje
        elif periodo == 'semana_passada':
            fim_semana_passada = hoje - timedelta(days=hoje.weekday() + 1)
            inicio_semana_passada = fim_semana_passada - timedelta(days=6)
            return inicio_semana_passada, fim_semana_passada
        elif periodo == 'este_mes':
            inicio_mes = hoje.replace(day=1)
            return inicio_mes, hoje
        elif periodo == 'mes_passado':
            if hoje.month == 1:
                inicio_mes_passado = hoje.replace(year=hoje.year-1, month=12, day=1)
                fim_mes_passado = hoje.replace(day=1) - timedelta(days=1)
            else:
                inicio_mes_passado = hoje.replace(month=hoje.month-1, day=1)
                fim_mes_passado = hoje.replace(day=1) - timedelta(days=1)
            return inicio_mes_passado, fim_mes_passado
        elif periodo == 'este_ano':
            inicio_ano = hoje.replace(month=1, day=1)
            return inicio_ano, hoje
        elif periodo == 'ano_passado':
            inicio_ano_passado = hoje.replace(year=hoje.year-1, month=1, day=1)
            fim_ano_passado = hoje.replace(year=hoje.year-1, month=12, day=31)
            return inicio_ano_passado, fim_ano_passado
        elif periodo == 'personalizado':
            return cleaned_data.get('data_inicio'), cleaned_data.get('data_fim')
        
        return None, None


# Views adicionais para funcionalidades específicas

@login_required
def marcar_parcela_paga(request, pk):
    """
    Marca uma parcela de honorário como paga
    """
    parcela = get_object_or_404(ParcelaHonorario, pk=pk)
    
    # Verificar permissões
    if not request.user.is_staff and parcela.honorario.processo.responsavel != request.user:
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('financeiro:detalhe_honorario', pk=parcela.honorario.pk)
    
    if request.method == 'POST':
        form = ParcelaHonorarioForm(request.POST, instance=parcela)
        if form.is_valid():
            parcela = form.save()
            if parcela.status == 'pago':
                parcela.marcar_como_paga()
            messages.success(request, 'Parcela atualizada com sucesso!')
            return redirect('financeiro:detalhe_honorario', pk=parcela.honorario.pk)
    else:
        form = ParcelaHonorarioForm(instance=parcela)
    
    context = {
        'form': form,
        'parcela': parcela,
        'honorario': parcela.honorario
    }
    
    return render(request, 'financeiro/parcela_form.html', context)


@login_required
def marcar_despesa_reembolsada(request, pk):
    """
    Marca uma despesa como reembolsada
    """
    despesa = get_object_or_404(Despesa, pk=pk)
    
    # Verificar permissões
    if not request.user.is_staff and despesa.processo.responsavel != request.user:
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('financeiro:detalhe_despesa', pk=despesa.pk)
    
    if request.method == 'POST':
        despesa.marcar_como_reembolsada()
        messages.success(request, 'Despesa marcada como reembolsada!')
        return redirect('financeiro:detalhe_despesa', pk=despesa.pk)
    
    context = {'despesa': despesa}
    return render(request, 'financeiro/confirmar_reembolso.html', context)


@login_required
def estatisticas_financeiras(request):
    """
    API para estatísticas financeiras (JSON)
    """
    # Filtrar dados por usuário se não for staff
    if request.user.is_staff:
        honorarios_qs = Honorario.objects.all()
        despesas_qs = Despesa.objects.all()
    else:
        honorarios_qs = Honorario.objects.filter(
            processo__responsavel=request.user
        )
        despesas_qs = Despesa.objects.filter(
            processo__responsavel=request.user
        )
    
    # Estatísticas de honorários
    honorarios_stats = {
        'total': honorarios_qs.count(),
        'valor_total': float(honorarios_qs.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')),
        'recebidos': honorarios_qs.filter(status_pagamento='pago').count(),
        'valor_recebido': float(honorarios_qs.filter(status_pagamento='pago').aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')),
        'pendentes': honorarios_qs.filter(status_pagamento='pendente').count(),
        'valor_pendente': float(honorarios_qs.filter(status_pagamento='pendente').aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')),
        'vencidos': honorarios_qs.filter(
            data_vencimento__lt=date.today(),
            status_pagamento__in=['pendente', 'parcial']
        ).count(),
    }
    
    # Estatísticas de despesas
    despesas_stats = {
        'total': despesas_qs.count(),
        'valor_total': float(despesas_qs.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')),
        'reembolsadas': despesas_qs.filter(status_reembolso='reembolsado').count(),
        'valor_reembolsado': float(despesas_qs.filter(status_reembolso='reembolsado').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')),
        'pendentes': despesas_qs.filter(status_reembolso='pendente').count(),
        'valor_pendente': float(despesas_qs.filter(status_reembolso='pendente').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')),
    }
    
    # Honorários por tipo de cobrança
    honorarios_por_tipo = list(
        honorarios_qs.values('tipo_cobranca')
        .annotate(
            total=Count('id'),
            valor=Sum('valor_total')
        )
        .order_by('-valor')
    )
    
    # Despesas por tipo
    despesas_por_tipo = list(
        despesas_qs.values('tipo_despesa')
        .annotate(
            total=Count('id'),
            valor=Sum('valor')
        )
        .order_by('-valor')
    )
    
    return JsonResponse({
        'honorarios': honorarios_stats,
        'despesas': despesas_stats,
        'honorarios_por_tipo': honorarios_por_tipo,
        'despesas_por_tipo': despesas_por_tipo,
    })


@login_required
def exportar_relatorio_financeiro(request):
    """
    Exporta relatório financeiro em CSV
    """
    import csv
    from django.utils.encoding import smart_str
    
    # Aplicar filtros da sessão ou parâmetros GET
    form = FiltroFinanceiroForm(request.GET, user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_financeiro.csv"'
    response.write('\ufeff')  # BOM para UTF-8
    
    writer = csv.writer(response, delimiter=';')
    
    # Cabeçalho
    writer.writerow([
        'Tipo', 'Processo', 'Cliente', 'Descrição', 'Valor', 'Data', 'Status'
    ])
    
    if form.is_valid():
        # Filtrar dados
        data_inicio, data_fim = RelatoriosFinanceirosView()._get_periodo_filtro(form.cleaned_data)
        
        # Filtrar dados por usuário se não for staff
        if request.user.is_staff:
            honorarios_qs = Honorario.objects.all()
            despesas_qs = Despesa.objects.all()
        else:
            honorarios_qs = Honorario.objects.filter(
                processo__responsavel=request.user
            )
            despesas_qs = Despesa.objects.filter(
                processo__responsavel=request.user
            )
        
        # Aplicar filtros de período
        if data_inicio:
            honorarios_qs = honorarios_qs.filter(data_vencimento__gte=data_inicio)
            despesas_qs = despesas_qs.filter(data_despesa__gte=data_inicio)
        if data_fim:
            honorarios_qs = honorarios_qs.filter(data_vencimento__lte=data_fim)
            despesas_qs = despesas_qs.filter(data_despesa__lte=data_fim)
        
        # Filtros adicionais
        processo = form.cleaned_data.get('processo')
        if processo:
            honorarios_qs = honorarios_qs.filter(processo=processo)
            despesas_qs = despesas_qs.filter(processo=processo)
        
        cliente = form.cleaned_data.get('cliente')
        if cliente:
            honorarios_qs = honorarios_qs.filter(cliente=cliente)
            despesas_qs = despesas_qs.filter(processo__cliente=cliente)
        
        # Escrever honorários
        for honorario in honorarios_qs.select_related('processo', 'cliente'):
            writer.writerow([
                'Honorário',
                smart_str(honorario.processo.numero_processo),
                smart_str(honorario.cliente.nome_razao_social),
                smart_str(honorario.get_tipo_cobranca_display()),
                str(honorario.valor_total).replace('.', ','),
                honorario.data_vencimento.strftime('%d/%m/%Y'),
                smart_str(honorario.get_status_pagamento_display())
            ])
        
        # Escrever despesas
        for despesa in despesas_qs.select_related('processo', 'processo__cliente'):
            writer.writerow([
                'Despesa',
                smart_str(despesa.processo.numero_processo),
                smart_str(despesa.processo.cliente.nome_razao_social),
                smart_str(despesa.descricao),
                str(despesa.valor).replace('.', ','),
                despesa.data_despesa.strftime('%d/%m/%Y'),
                smart_str(despesa.get_status_reembolso_display())
            ])
    
    return response


class ContaBancariaListView(LoginRequiredMixin, ListView):
    """
    Listagem de contas bancárias
    """
    model = ContaBancaria
    template_name = 'financeiro/contas_bancarias.html'
    context_object_name = 'contas'
    paginate_by = 20
    
    def get_queryset(self):
        return ContaBancaria.objects.filter(ativa=True).order_by('nome_conta')


class ContaBancariaCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de nova conta bancária
    """
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = 'financeiro/conta_bancaria_form.html'
    success_url = reverse_lazy('financeiro:contas_bancarias')
    
    def form_valid(self, form):
        messages.success(self.request, 'Conta bancária cadastrada com sucesso!')
        return super().form_valid(form)


class ContaBancariaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edição de conta bancária
    """
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = 'financeiro/conta_bancaria_form.html'
    success_url = reverse_lazy('financeiro:contas_bancarias')
    
    def form_valid(self, form):
        messages.success(self.request, 'Conta bancária atualizada com sucesso!')
        return super().form_valid(form)


@login_required
def transacoes_view(request):
    """
    View para listagem unificada de transações financeiras (honorários e despesas)
    com filtros e paginação
    """
    # Filtros
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    
    # Query base para honorários (parcelas)
    parcelas_query = ParcelaHonorario.objects.select_related('honorario', 'honorario__cliente', 'honorario__processo')
    
    # Query base para despesas
    despesas_query = Despesa.objects.all()
    
    # Aplicar filtros de data
    if data_inicial:
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        parcelas_query = parcelas_query.filter(data_vencimento__gte=data_inicial_obj)
        despesas_query = despesas_query.filter(data_despesa__gte=data_inicial_obj)
    
    if data_final:
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
        parcelas_query = parcelas_query.filter(data_vencimento__lte=data_final_obj)
        despesas_query = despesas_query.filter(data_despesa__lte=data_final_obj)
    
    # Aplicar filtros de status
    if status == 'pago':
        parcelas_query = parcelas_query.filter(status_pagamento='pago')
        despesas_query = despesas_query.filter(status_reembolso='reembolsado')
    elif status == 'pendente':
        parcelas_query = parcelas_query.filter(status_pagamento='pendente', data_vencimento__gte=timezone.now().date())
        despesas_query = despesas_query.filter(status_reembolso='pendente')
    elif status == 'vencido':
        parcelas_query = parcelas_query.filter(status_pagamento='pendente', data_vencimento__lt=timezone.now().date())
        despesas_query = despesas_query.none()  # Despesas não têm conceito de vencimento
    
    # Preparar listas de transações
    transacoes = []
    
    # Adicionar honorários se não filtrado apenas para despesas
    if tipo != 'despesa':
        for parcela in parcelas_query:
            transacao = {
                'pk': parcela.pk,
                'tipo': 'honorario',
                'valor': parcela.valor,
                'data_vencimento': parcela.data_vencimento,
                'status_pagamento': parcela.status_pagamento,
                'processo': parcela.honorario.processo,
                'cliente': parcela.honorario.cliente,
                'is_vencido': parcela.data_vencimento < timezone.now().date() and parcela.status_pagamento != 'pago',
                'data_ordenacao': parcela.data_vencimento
            }
            transacoes.append(transacao)
    
    # Adicionar despesas se não filtrado apenas para honorários
    if tipo != 'honorario':
        for despesa in despesas_query:
            transacao = {
                'pk': despesa.pk,
                'tipo': 'despesa',
                'valor': despesa.valor,
                'data_despesa': despesa.data_despesa,
                'status_reembolso': despesa.status_reembolso,
                'descricao': despesa.descricao,
                'tipo_despesa': despesa.tipo_despesa,
                'get_tipo_despesa_display': despesa.get_tipo_despesa_display(),
                'get_status_reembolso_display': despesa.get_status_reembolso_display(),
                'data_ordenacao': despesa.data_despesa
            }
            transacoes.append(transacao)
    
    # Ordenar por data (mais recente primeiro)
    transacoes.sort(key=lambda x: x['data_ordenacao'], reverse=True)
    
    # Calcular totais
    total_receitas = sum(t['valor'] for t in transacoes if t['tipo'] == 'honorario')
    total_despesas = sum(t['valor'] for t in transacoes if t['tipo'] == 'despesa')
    saldo_liquido = total_receitas - total_despesas
    total_transacoes = len(transacoes)
    
    # Paginação
    paginator = Paginator(transacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transacoes': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo_liquido': saldo_liquido,
        'total_transacoes': total_transacoes,
    }
    
    return render(request, 'financeiro/transacoes.html', context)
