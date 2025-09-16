from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404
from .models import Documento
from processos.models import Processo


class DocumentoListView(LoginRequiredMixin, ListView):
    model = Documento
    template_name = 'documentos/lista.html'
    context_object_name = 'documentos'
    paginate_by = 20
    login_url = '/login/'


class DocumentoDetailView(LoginRequiredMixin, DetailView):
    model = Documento
    template_name = 'documentos/detalhe.html'
    login_url = '/login/'


class DocumentoUploadView(LoginRequiredMixin, CreateView):
    model = Documento
    template_name = 'documentos/upload.html'
    fields = ['processo', 'tipo_documento', 'descricao', 'arquivo']
    login_url = '/login/'
    success_url = reverse_lazy('documentos:lista')
    
    def form_valid(self, form):
        form.instance.usuario_upload = self.request.user
        messages.success(self.request, 'Documento enviado com sucesso!')
        return super().form_valid(form)


class DocumentoDownloadView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    
    def get(self, request, *args, **kwargs):
        documento = get_object_or_404(Documento, pk=kwargs['pk'])
        # Implementar download do arquivo
        return HttpResponse('Download - Em desenvolvimento')


class DocumentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Documento
    template_name = 'documentos/confirmar_exclusao.html'
    success_url = reverse_lazy('documentos:lista')
    login_url = '/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Documento excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class DocumentosProcessoView(LoginRequiredMixin, ListView):
    model = Documento
    template_name = 'documentos/processo.html'
    context_object_name = 'documentos'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        self.processo = get_object_or_404(Processo, pk=self.kwargs['processo_id'])
        return self.processo.documentos.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processo'] = self.processo
        return context
