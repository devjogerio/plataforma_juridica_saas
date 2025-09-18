from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from .models import Processo, Andamento, Prazo
from .forms import ProcessoForm, ProcessoPrimeiroForm
from clientes.models import Cliente
from django.db.models import Q


class ProcessoListView(LoginRequiredMixin, ListView):
    """
    Lista todos os processos com filtros e paginação
    """
    model = Processo
    template_name = 'processos/lista.html'
    context_object_name = 'processos'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        """
        Otimiza queries com select_related e prefetch_related para melhor performance
        """
        queryset = Processo.objects.select_related(
            'cliente', 
            'usuario_responsavel'
        ).prefetch_related(
            'andamentos__usuario',
            'prazos__usuario_responsavel'
        )
        
        # Filtros
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        area_direito = self.request.GET.get('area_direito')
        
        if search:
            queryset = queryset.filter(
                Q(numero_processo__icontains=search) |
                Q(cliente__nome_razao_social__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
            
        if area_direito:
            queryset = queryset.filter(area_direito=area_direito)
            
        return queryset.order_by('-created_at')


class ProcessoDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe detalhes de um processo específico
    """
    model = Processo
    template_name = 'processos/detalhe.html'
    context_object_name = 'processo'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dados relacionados ao contexto com queries otimizadas
        """
        context = super().get_context_data(**kwargs)
        processo = self.get_object()
        
        # Últimos andamentos com select_related otimizado
        context['ultimos_andamentos'] = processo.andamentos.select_related('usuario').order_by('-data_andamento')[:5]
        
        # Prazos pendentes com select_related otimizado
        context['prazos_pendentes'] = processo.prazos.select_related('usuario_responsavel').filter(cumprido=False).order_by('data_limite')
        
        # Documentos com select_related otimizado
        context['documentos'] = processo.documentos.select_related('usuario_upload').order_by('-created_at')[:10]
        
        return context


class ProcessoCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo processo
    """
    model = Processo
    form_class = ProcessoForm
    template_name = 'processos/form.html'
    login_url = '/login/'
    
    def get_form_kwargs(self):
        """
        Passa o usuário atual para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        """
        Define valores iniciais baseados nos parâmetros GET
        """
        initial = super().get_initial()
        
        # Se há um cliente especificado na URL
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                initial['cliente'] = cliente
            except Cliente.DoesNotExist:
                pass
        
        return initial
    
    def form_valid(self, form):
        """
        Processa o formulário válido e exibe mensagem de sucesso detalhada
        """
        response = super().form_valid(form)
        
        # Mensagem de sucesso com detalhes do processo criado
        messages.success(
            self.request, 
            f'✅ Processo criado com sucesso!<br>'
            f'<strong>Número:</strong> {self.object.numero_processo}<br>'
            f'<strong>Cliente:</strong> {self.object.cliente.nome_razao_social}<br>'
            f'<strong>Área:</strong> {self.object.get_area_direito_display()}'
        )
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.pk})


class ProcessoPrimeiroCreateView(LoginRequiredMixin, CreateView):
    """
    View específica para criação do primeiro processo.
    Inclui orientações e validações especiais para novos usuários.
    """
    model = Processo
    form_class = ProcessoPrimeiroForm
    template_name = 'processos/primeiro_processo_form.html'
    login_url = '/login/'
    
    def get_form_kwargs(self):
        """
        Passa o usuário atual para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        """
        Define valores iniciais para o primeiro processo
        """
        initial = super().get_initial()
        
        # Se há um cliente especificado na URL
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                initial['cliente'] = cliente
            except Cliente.DoesNotExist:
                pass
        
        return initial
    
    def get_context_data(self, **kwargs):
        """
        Adiciona contexto específico para o primeiro processo
        """
        context = super().get_context_data(**kwargs)
        context['is_primeiro_processo'] = True
        context['total_processos'] = Processo.objects.filter(
            usuario_responsavel=self.request.user
        ).count()
        return context
    
    def form_valid(self, form):
        """
        Processa o formulário válido com mensagem especial
        """
        messages.success(
            self.request, 
            'Parabéns! Seu primeiro processo foi criado com sucesso! '
            'Agora você pode adicionar andamentos, prazos e documentos.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.pk})


class ProcessoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um processo existente
    """
    model = Processo
    template_name = 'processos/form.html'
    fields = ['numero_processo', 'tipo_processo', 'area_direito', 'status', 'valor_causa', 
              'comarca_tribunal', 'vara_orgao', 'data_inicio', 'data_encerramento', 'cliente', 'observacoes']
    login_url = '/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Processo atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.pk})


class ProcessoDeleteView(LoginRequiredMixin, DeleteView):
    """
    Exclui um processo
    """
    model = Processo
    template_name = 'processos/confirmar_exclusao.html'
    success_url = reverse_lazy('processos:lista')
    login_url = '/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Processo excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class AndamentoListView(LoginRequiredMixin, ListView):
    """
    Lista andamentos de um processo específico
    """
    model = Andamento
    template_name = 'processos/andamentos.html'
    context_object_name = 'andamentos'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        self.processo = get_object_or_404(Processo, pk=self.kwargs['pk'])
        return self.processo.andamentos.select_related('usuario').order_by('-data_andamento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processo'] = self.processo
        return context


class AndamentoCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo andamento para um processo
    """
    model = Andamento
    template_name = 'processos/andamento_form.html'
    fields = ['data_andamento', 'tipo_andamento', 'descricao']
    login_url = '/login/'
    
    def form_valid(self, form):
        self.processo = get_object_or_404(Processo, pk=self.kwargs['pk'])
        form.instance.processo = self.processo
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Andamento adicionado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('processos:andamentos', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processo'] = get_object_or_404(Processo, pk=self.kwargs['pk'])
        return context


class PrazoListView(LoginRequiredMixin, ListView):
    """
    Lista prazos de um processo específico
    """
    model = Prazo
    template_name = 'processos/prazos.html'
    context_object_name = 'prazos'
    login_url = '/login/'
    
    def get_queryset(self):
        self.processo = get_object_or_404(Processo, pk=self.kwargs['pk'])
        return self.processo.prazos.select_related('usuario_responsavel').order_by('data_limite')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processo'] = self.processo
        return context


class PrazoCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo prazo para um processo
    """
    model = Prazo
    template_name = 'processos/prazo_form.html'
    fields = ['tipo_prazo', 'data_limite', 'descricao', 'usuario_responsavel']
    login_url = '/login/'
    
    def form_valid(self, form):
        self.processo = get_object_or_404(Processo, pk=self.kwargs['pk'])
        form.instance.processo = self.processo
        messages.success(self.request, 'Prazo adicionado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('processos:prazos', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processo'] = get_object_or_404(Processo, pk=self.kwargs['pk'])
        return context


class CumprirPrazoView(LoginRequiredMixin, TemplateView):
    """
    Marca um prazo como cumprido
    """
    login_url = '/login/'
    
    def post(self, request, *args, **kwargs):
        prazo = get_object_or_404(Prazo, pk=kwargs['pk'])
        prazo.cumprido = True
        prazo.data_cumprimento = timezone.now().date()
        prazo.save()
        
        messages.success(request, 'Prazo marcado como cumprido!')
        return redirect('processos:prazos', pk=prazo.processo.pk)
