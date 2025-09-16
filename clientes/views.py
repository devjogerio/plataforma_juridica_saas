from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from .models import Cliente, InteracaoCliente
from .forms import ClienteForm, InteracaoClienteForm, ClienteFilterForm
from .filters import ClienteFilter
from .audit import registrar_criacao_cliente, registrar_visualizacao_cliente
from processos.models import Processo


class ClienteListView(LoginRequiredMixin, ListView):
    """
    View para listagem de clientes com filtros e paginação
    """
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Filtra clientes baseado nos parâmetros de busca com otimizações de performance
        """
        # Otimização: select_related para evitar N+1 queries
        queryset = Cliente.objects.select_related('usuario_criacao').prefetch_related(
            'processos',
            'interacoes'
        )
        
        # Anotar com dados calculados
        queryset = queryset.annotate(
            total_processos=Count('processos', distinct=True),
            processos_ativos=Count('processos', filter=Q(processos__status='ativo'), distinct=True),
            valor_total_causas=Sum('processos__valor_causa')
        )
        
        # Filtros de busca
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nome_razao_social__icontains=q) |
                Q(cpf_cnpj__icontains=q) |
                Q(email__icontains=q)
            )
        
        # Filtro por tipo de pessoa
        tipo_pessoa = self.request.GET.get('tipo_pessoa')
        if tipo_pessoa:
            queryset = queryset.filter(tipo_pessoa=tipo_pessoa)
        
        # Filtro por UF
        uf = self.request.GET.get('uf')
        if uf:
            queryset = queryset.filter(uf=uf)
        
        # Filtro por status ativo
        ativo = self.request.GET.get('ativo')
        if ativo == 'true':
            queryset = queryset.filter(ativo=True)
        elif ativo == 'false':
            queryset = queryset.filter(ativo=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Adiciona estatísticas ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        base_queryset = Cliente.objects.all()
        
        # Remover filtro por usuário - todos os clientes são visíveis
        
        context.update({
            'total_clientes': base_queryset.count(),
            'clientes_ativos': base_queryset.filter(ativo=True).count(),
            'clientes_pf': base_queryset.filter(tipo_pessoa='PF').count(),
            'clientes_pj': base_queryset.filter(tipo_pessoa='PJ').count(),
        })
        
        return context


class ClienteDetailView(LoginRequiredMixin, DetailView):
    """
    View para exibir detalhes de um cliente
    """
    model = Cliente
    template_name = 'clientes/detalhe.html'
    context_object_name = 'cliente'
    
    def get_queryset(self):
        """
        Otimiza queries para evitar N+1 problems
        """
        return Cliente.objects.select_related('usuario_criacao').prefetch_related(
            'processos__tipo_processo',
            'processos__tribunal',
            'interacoes__usuario'
        ).annotate(
            total_processos=Count('processos', distinct=True),
            processos_ativos=Count('processos', filter=Q(processos__status='ativo'), distinct=True),
            prazos_pendentes=Count('processos__prazos', filter=Q(processos__prazos__status='pendente'), distinct=True),
            valor_total_causas=Sum('processos__valor_causa')
        )
    
    def get_context_data(self, **kwargs):
        """
        Adiciona processos relacionados ao contexto
        """
        context = super().get_context_data(**kwargs)
        
        # Processos do cliente
        processos = Processo.objects.filter(
            cliente=self.object
        ).select_related(
            'tipo_processo', 'area_direito', 'responsavel'
        ).order_by('-data_inicio')[:10]
        
        context['processos'] = processos
        
        return context


class ClienteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View para criar novo cliente
    """
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_message = "Cliente cadastrado com sucesso!"
    
    def form_valid(self, form):
        """
        Salvar cliente com dados adicionais
        """
        # Remover associação com usuário
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('clientes:detalhe', kwargs={'pk': self.object.pk})


class ClienteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View para editar cliente existente
    """
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_message = "Cliente atualizado com sucesso!"
    
    def get_queryset(self):
        """
        Filtra clientes
        """
        queryset = Cliente.objects.all()
        
        return queryset
    
    def get_success_url(self):
        return reverse('clientes:detalhe', kwargs={'pk': self.object.pk})


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """
    View para excluir cliente
    """
    model = Cliente
    template_name = 'clientes/confirmar_exclusao.html'
    
    def get_queryset(self):
        """
        Retornar todos os clientes
        """
        return Cliente.objects.all()
    
    def delete(self, request, *args, **kwargs):
        """
        Adiciona mensagem de sucesso após exclusão
        """
        cliente = self.get_object()
        messages.success(request, f'Cliente "{cliente.nome_razao_social}" excluído com sucesso!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('clientes:lista')


@login_required
@require_http_methods(["GET"])
def busca_rapida_clientes(request):
    """
    API para busca rápida de clientes (usado em selects)
    """
    q = request.GET.get('q', '')
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    # Filtrar clientes
    queryset = Cliente.objects.filter(ativo=True)
    
    clientes = queryset.filter(
        Q(nome_razao_social__icontains=q) |
        Q(cpf_cnpj__icontains=q)
    ).values(
        'id', 'nome_razao_social', 'cpf_cnpj', 'tipo_pessoa'
    )[:10]
    
    results = []
    for cliente in clientes:
        nome_display = cliente['nome_razao_social']
        
        results.append({
            'id': cliente['id'],
            'text': nome_display,
            'cpf_cnpj': cliente['cpf_cnpj'],
            'tipo_pessoa': cliente['tipo_pessoa']
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def estatisticas_clientes_api(request):
    """
    API para estatísticas de clientes
    """
    # Obter todos os clientes
    queryset = Cliente.objects.all()
    
    # Estatísticas básicas
    stats = {
        'total': queryset.count(),
        'ativos': queryset.filter(ativo=True).count(),
        'inativos': queryset.filter(ativo=False).count(),
        'pessoa_fisica': queryset.filter(tipo_pessoa='PF').count(),
        'pessoa_juridica': queryset.filter(tipo_pessoa='PJ').count(),
    }
    
    # Clientes por estado
    por_estado = list(
        queryset.values('uf')
        .annotate(total=Count('id'))
        .filter(uf__isnull=False)
        .order_by('-total')[:10]
    )
    
    # Clientes cadastrados por mês (últimos 12 meses)
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    hoje = timezone.now().date()
    inicio_periodo = hoje - timedelta(days=365)
    
    por_mes = list(
        queryset.filter(created_at__date__gte=inicio_periodo)
        .extra(select={'mes': "DATE_FORMAT(created_at, '%%Y-%%m')"})
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    
    return JsonResponse({
        'estatisticas': stats,
        'por_estado': por_estado,
        'por_mes': por_mes
    })


@login_required
def dashboard_clientes(request):
    """
    Dashboard específico para clientes
    """
    # Filtrar clientes
    queryset = Cliente.objects.all()
    
    # Clientes recentes
    clientes_recentes = queryset.order_by('-created_at')[:5]
    
    # Clientes com mais processos
    clientes_top = queryset.annotate(
        total_processos=Count('processos')
    ).filter(total_processos__gt=0).order_by('-total_processos')[:5]
    
    # Estatísticas
    total_clientes = queryset.count()
    clientes_ativos = queryset.filter(ativo=True).count()
    clientes_pf = queryset.filter(tipo_pessoa='PF').count()
    clientes_pj = queryset.filter(tipo_pessoa='PJ').count()
    
    context = {
        'clientes_recentes': clientes_recentes,
        'clientes_top': clientes_top,
        'total_clientes': total_clientes,
        'clientes_ativos': clientes_ativos,
        'clientes_pf': clientes_pf,
        'clientes_pj': clientes_pj,
    }
    
    return render(request, 'clientes/dashboard.html', context)


# Views baseadas em função (alternativa às class-based views)

@login_required
def lista_clientes(request):
    """
    Lista de clientes com filtros
    """
    # Filtrar clientes
    queryset = Cliente.objects.all()
    
    # Aplicar filtros
    filtros = ClienteFilter(request.GET, queryset=queryset)
    clientes = filtros.qs
    
    # Paginação
    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    base_queryset = Cliente.objects.all()
    # Obter todos os clientes para estatísticas
    
    context = {
        'clientes': page_obj,
        'total_clientes': base_queryset.count(),
        'clientes_ativos': base_queryset.filter(ativo=True).count(),
        'clientes_pf': base_queryset.filter(tipo_pessoa='PF').count(),
        'clientes_pj': base_queryset.filter(tipo_pessoa='PJ').count(),
    }
    
    return render(request, 'clientes/lista.html', context)


@login_required
def detalhe_cliente(request, pk):
    """
    Detalhe de um cliente específico
    """
    # Buscar cliente
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Registrar auditoria da visualização (apenas para clientes importantes ou sensíveis)
    # Pode ser configurado baseado em critérios específicos
    if cliente.ativo or hasattr(cliente, 'is_vip'):
        registrar_visualizacao_cliente(cliente, usuario=request.user, request=request)
    
    # Buscar processos relacionados
    processos = cliente.processos.all().order_by('-created_at')[:10]
    
    context = {
        'cliente': cliente,
        'processos': processos,
    }
    
    return render(request, 'clientes/detalhe.html', context)


@login_required
def criar_cliente(request):
    """
    View de função para criar cliente
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            
            # Registrar auditoria da criação
            registrar_criacao_cliente(cliente, usuario=request.user, request=request)
            
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('clientes:detalhe', pk=cliente.pk)
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/form.html', {'form': form})


@login_required
def editar_cliente(request, pk):
    """
    View de função para editar cliente
    """
    # Buscar cliente
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('clientes:detalhe', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/form.html', {'form': form})


@login_required
def excluir_cliente(request, pk):
    """
    View de função para excluir cliente
    """
    # Buscar cliente
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        nome = cliente.nome_razao_social
        cliente.delete()
        messages.success(request, f'Cliente "{nome}" excluído com sucesso!')
        return redirect('clientes:lista')
    
    return render(request, 'clientes/confirmar_exclusao.html', {'cliente': cliente})


@login_required
def adicionar_interacao(request, cliente_id):
    """
    View para adicionar interação com cliente
    """
    # Buscar cliente
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    if request.method == 'POST':
        form = InteracaoClienteForm(request.POST)
        if form.is_valid():
            interacao = form.save(commit=False)
            interacao.cliente = cliente
            interacao.usuario = request.user
            interacao.save()
            messages.success(request, 'Interação adicionada com sucesso!')
            return redirect('clientes:detalhe', cliente_id=cliente.pk)
    else:
        form = InteracaoClienteForm()
    
    return render(request, 'clientes/interacao_form.html', {
        'form': form,
        'cliente': cliente
    })


@login_required
@require_http_methods(["POST"])
def toggle_ativo_cliente(request, cliente_id):
    """
    View AJAX para ativar/desativar cliente
    """
    # Buscar cliente
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    # Toggle status ativo
    cliente.ativo = not cliente.ativo
    cliente.save()
    
    return JsonResponse({
        'success': True,
        'ativo': cliente.ativo,
        'message': f'Cliente {"ativado" if cliente.ativo else "desativado"} com sucesso!'
    })


@login_required
@require_http_methods(["GET"])
def buscar_clientes_ajax(request):
    """
    Busca AJAX para clientes
    """
    q = request.GET.get('q', '')
    
    if len(q) < 2:
        return JsonResponse({'clientes': []})
    
    # Filtrar clientes
    queryset = Cliente.objects.filter(ativo=True)
    
    clientes = queryset.filter(
        Q(nome_razao_social__icontains=q) |
        Q(cpf_cnpj__icontains=q)
    ).values(
        'id', 'nome_razao_social', 'cpf_cnpj', 'tipo_pessoa'
    )[:20]
    
    return JsonResponse({'clientes': list(clientes)})
