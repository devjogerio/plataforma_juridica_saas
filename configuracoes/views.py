from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import TipoProcesso, AreaDireito, StatusProcesso, ModeloDocumento, ConfiguracaoSistema


class ConfiguracoesDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'configuracoes/dashboard.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        context['total_tipos_processo'] = TipoProcesso.objects.filter(ativo=True).count()
        context['total_areas_direito'] = AreaDireito.objects.filter(ativo=True).count()
        context['total_status_processo'] = StatusProcesso.objects.filter(ativo=True).count()
        context['total_modelos_documento'] = ModeloDocumento.objects.filter(ativo=True).count()
        context['total_configuracoes'] = ConfiguracaoSistema.objects.count()
        
        # Itens recentes
        context['tipos_processo_recentes'] = TipoProcesso.objects.filter(ativo=True).order_by('-criado_em')[:5]
        context['areas_direito_recentes'] = AreaDireito.objects.filter(ativo=True).order_by('-criado_em')[:5]
        context['modelos_mais_usados'] = ModeloDocumento.objects.filter(ativo=True).order_by('-vezes_usado')[:5]
        
        return context


class TipoProcessoListView(LoginRequiredMixin, ListView):
    model = TipoProcesso
    template_name = 'configuracoes/tipos_processo.html'
    context_object_name = 'tipos_processo'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = TipoProcesso.objects.all().order_by('ordem', 'nome')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(codigo__icontains=search) |
                Q(descricao__icontains=search)
            )
        
        ativo = self.request.GET.get('ativo')
        if ativo:
            queryset = queryset.filter(ativo=ativo == 'true')
        
        return queryset


class TipoProcessoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TipoProcesso
    template_name = 'configuracoes/tipo_processo_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:tipos_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Tipo de processo criado com sucesso!')
        return super().form_valid(form)


class TipoProcessoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TipoProcesso
    template_name = 'configuracoes/tipo_processo_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:tipos_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de processo atualizado com sucesso!')
        return super().form_valid(form)


class TipoProcessoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TipoProcesso
    template_name = 'configuracoes/confirmar_exclusao.html'
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:tipos_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de processo excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class AreaDireitoListView(LoginRequiredMixin, ListView):
    model = AreaDireito
    template_name = 'configuracoes/areas_direito.html'
    context_object_name = 'areas_direito'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = AreaDireito.objects.all().order_by('ordem', 'nome')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(codigo__icontains=search) |
                Q(descricao__icontains=search)
            )
        
        ativo = self.request.GET.get('ativo')
        if ativo:
            queryset = queryset.filter(ativo=ativo == 'true')
        
        return queryset


class AreaDireitoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AreaDireito
    template_name = 'configuracoes/area_direito_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:areas_direito')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Área do direito criada com sucesso!')
        return super().form_valid(form)


class AreaDireitoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AreaDireito
    template_name = 'configuracoes/area_direito_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:areas_direito')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Área do direito atualizada com sucesso!')
        return super().form_valid(form)


class AreaDireitoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AreaDireito
    template_name = 'configuracoes/confirmar_exclusao.html'
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:areas_direito')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Área do direito excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class StatusProcessoListView(LoginRequiredMixin, ListView):
    model = StatusProcesso
    template_name = 'configuracoes/status_processo.html'
    context_object_name = 'status_processo'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = StatusProcesso.objects.all().order_by('ordem', 'nome')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(codigo__icontains=search) |
                Q(descricao__icontains=search)
            )
        
        ativo = self.request.GET.get('ativo')
        if ativo:
            queryset = queryset.filter(ativo=ativo == 'true')
        
        return queryset


class StatusProcessoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = StatusProcesso
    template_name = 'configuracoes/status_processo_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'is_inicial', 'is_final', 'permite_edicao', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:status_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Status de processo criado com sucesso!')
        return super().form_valid(form)


class StatusProcessoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StatusProcesso
    template_name = 'configuracoes/status_processo_form.html'
    fields = ['nome', 'descricao', 'codigo', 'cor', 'icone', 'is_inicial', 'is_final', 'permite_edicao', 'ativo', 'ordem']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:status_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Status de processo atualizado com sucesso!')
        return super().form_valid(form)


class StatusProcessoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = StatusProcesso
    template_name = 'configuracoes/confirmar_exclusao.html'
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:status_processo')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Status de processo excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class ModeloDocumentoListView(LoginRequiredMixin, ListView):
    model = ModeloDocumento
    template_name = 'configuracoes/modelos_documentos.html'
    context_object_name = 'modelos_documento'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = ModeloDocumento.objects.select_related('criado_por').prefetch_related('areas_direito', 'tipos_processo')
        
        # Filtrar por usuário se não for staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(Q(criado_por=self.request.user) | Q(publico=True))
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(categoria__icontains=search) |
                Q(descricao__icontains=search)
            )
        
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        ativo = self.request.GET.get('ativo')
        if ativo:
            queryset = queryset.filter(ativo=ativo == 'true')
        
        return queryset.order_by('-ultimo_uso', '-criado_em')


class ModeloDocumentoCreateView(LoginRequiredMixin, CreateView):
    model = ModeloDocumento
    template_name = 'configuracoes/modelo_documento_form.html'
    fields = ['nome', 'descricao', 'categoria', 'conteudo', 'tipo_arquivo', 'publico', 'ativo', 'areas_direito', 'tipos_processo']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:modelos_documentos')
    
    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Modelo de documento criado com sucesso!')
        return super().form_valid(form)


class ModeloDocumentoUpdateView(LoginRequiredMixin, UpdateView):
    model = ModeloDocumento
    template_name = 'configuracoes/modelo_documento_form.html'
    fields = ['nome', 'descricao', 'categoria', 'conteudo', 'tipo_arquivo', 'publico', 'ativo', 'areas_direito', 'tipos_processo']
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:modelos_documentos')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(criado_por=self.request.user)
        return queryset
    
    def form_valid(self, form):
        messages.success(self.request, 'Modelo de documento atualizado com sucesso!')
        return super().form_valid(form)


class ModeloDocumentoDeleteView(LoginRequiredMixin, DeleteView):
    model = ModeloDocumento
    template_name = 'configuracoes/confirmar_exclusao.html'
    login_url = '/login/'
    success_url = reverse_lazy('configuracoes:modelos_documentos')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(criado_por=self.request.user)
        return queryset
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Modelo de documento excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class ConfiguracoesSistemaView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ConfiguracaoSistema
    template_name = 'configuracoes/sistema.html'
    context_object_name = 'configuracoes'
    login_url = '/login/'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return ConfiguracaoSistema.objects.all().order_by('categoria', 'chave')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupar configurações por categoria
        configuracoes_por_categoria = {}
        for config in context['configuracoes']:
            if config.categoria not in configuracoes_por_categoria:
                configuracoes_por_categoria[config.categoria] = []
            configuracoes_por_categoria[config.categoria].append(config)
        
        context['configuracoes_por_categoria'] = configuracoes_por_categoria
        return context


def atualizar_configuracao(request):
    """View AJAX para atualizar configurações do sistema"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permissão negada'})
    
    if request.method == 'POST':
        chave = request.POST.get('chave')
        valor = request.POST.get('valor')
        
        try:
            config = get_object_or_404(ConfiguracaoSistema, chave=chave, editavel=True)
            config.valor = valor
            config.atualizado_por = request.user
            config.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Configuração atualizada com sucesso!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Erro ao atualizar configuração: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})
