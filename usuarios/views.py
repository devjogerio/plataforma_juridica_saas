from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.contrib.auth import authenticate, update_session_auth_hash
from .models import Usuario, PreferenciaUsuario


class UsuarioListView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/lista.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    login_url = '/login/'


class UsuarioDetailView(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'usuarios/detalhe.html'
    login_url = '/login/'


class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    template_name = 'usuarios/form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario']
    login_url = '/login/'
    success_url = reverse_lazy('usuarios:lista')


class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario
    template_name = 'usuarios/form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario']
    login_url = '/login/'
    success_url = reverse_lazy('usuarios:lista')


class PerfilView(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'usuarios/perfil.html'
    login_url = '/login/'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Calcular estatísticas do usuário
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Importar modelos necessários
        from processos.models import Processo, Andamento, Prazo
        
        # Verificar se o usuário é cliente ou advogado/administrador
        if user.is_cliente:
            # Para usuários do tipo cliente, buscar processos onde ele é o cliente
            # Primeiro, verificar se existe um Cliente associado a este usuário
            from clientes.models import Cliente
            try:
                cliente = Cliente.objects.get(email=user.email)
                
                # Estatísticas de processos - processos onde o usuário é o cliente
                user.total_processos = Processo.objects.filter(cliente=cliente).count()
                user.processos_ativos = Processo.objects.filter(cliente=cliente, status='ativo').count()
                
                # Prazos dos processos do cliente
                user.prazos_pendentes = Prazo.objects.filter(
                    processo__cliente=cliente,
                    cumprido=False
                ).count()
                
                # Andamentos dos processos do cliente
                user.andamentos_mes = Andamento.objects.filter(
                    processo__cliente=cliente,
                    created_at__gte=inicio_mes
                ).count()
                
                # Atividades recentes dos processos do cliente
                atividades_recentes = Andamento.objects.filter(
                    processo__cliente=cliente
                ).select_related('processo').order_by('-created_at')[:10]
                
            except Cliente.DoesNotExist:
                # Se não encontrar cliente associado, zerar estatísticas
                user.total_processos = 0
                user.processos_ativos = 0
                user.prazos_pendentes = 0
                user.andamentos_mes = 0
                atividades_recentes = []
        else:
            # Para advogados e administradores - processos onde o usuário é responsável
            user.total_processos = Processo.objects.filter(
                usuario_responsavel=user
            ).count()
            
            user.processos_ativos = Processo.objects.filter(
                usuario_responsavel=user,
                status='ativo'
            ).count()
            
            # Estatísticas de prazos
            user.prazos_pendentes = Prazo.objects.filter(
                Q(usuario_responsavel=user) | Q(processo__usuario_responsavel=user),
                cumprido=False
            ).count()
            
            # Andamentos do mês
            user.andamentos_mes = Andamento.objects.filter(
                Q(usuario=user) | Q(processo__usuario_responsavel=user),
                created_at__gte=inicio_mes
            ).count()
            
            # Atividades recentes (últimos 10 andamentos)
            atividades_recentes = Andamento.objects.filter(
                Q(usuario=user) | Q(processo__usuario_responsavel=user)
            ).select_related('processo').order_by('-created_at')[:10]
        
        # Formatar atividades para o template
        context['atividades_recentes'] = []
        for andamento in atividades_recentes:
            context['atividades_recentes'].append({
                'titulo': f'Andamento - {andamento.processo.numero_processo}',
                'descricao': andamento.descricao[:100] + '...' if len(andamento.descricao) > 100 else andamento.descricao,
                'data': andamento.created_at,
                'tipo': 'Andamento'
            })
        
        return context


class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Usuario
    template_name = 'usuarios/editar_perfil.html'
    fields = ['first_name', 'last_name', 'email']
    login_url = '/login/'
    success_url = reverse_lazy('usuarios:perfil')
    
    def get_object(self):
        return self.request.user


class PermissoesView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/permissoes.html'
    login_url = '/login/'


class UsuarioPermissoesView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/usuario_permissoes.html'
    login_url = '/login/'


class PreferenciasView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/preferencias.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preferencias'] = self.request.user.get_preferencias()
        return context
    
    def post(self, request, *args, **kwargs):
        preferencias = request.user.get_preferencias()
        
        # Atualizar configurações de interface
        preferencias.tema = request.POST.get('tema', 'light')
        preferencias.idioma = request.POST.get('idioma', 'pt-br')
        preferencias.timezone = request.POST.get('timezone', 'America/Sao_Paulo')
        preferencias.items_por_pagina = int(request.POST.get('items_por_pagina', 20))
        preferencias.sidebar_collapsed = request.POST.get('sidebar_collapsed') == 'on'
        
        # Atualizar configurações de notificações
        preferencias.notificacoes_email = request.POST.get('notificacoes_email') == 'on'
        preferencias.notificacoes_prazos = request.POST.get('notificacoes_prazos') == 'on'
        preferencias.notificacoes_sistema = request.POST.get('notificacoes_sistema') == 'on'
        preferencias.notificacoes_marketing = request.POST.get('notificacoes_marketing') == 'on'
        
        # Atualizar configurações de relatórios
        preferencias.formato_data_preferido = request.POST.get('formato_data_preferido', 'dd/mm/yyyy')
        preferencias.formato_moeda_preferido = request.POST.get('formato_moeda_preferido', 'BRL')
        
        # Atualizar configurações de widgets do dashboard
        dashboard_widgets = {
            'processos_recentes': {
                'enabled': request.POST.get('widget_processos_recentes') == 'on',
                'order': 1
            },
            'prazos_proximos': {
                'enabled': request.POST.get('widget_prazos_proximos') == 'on',
                'order': 2
            },
            'estatisticas_gerais': {
                'enabled': request.POST.get('widget_estatisticas_gerais') == 'on',
                'order': 3
            },
            'grafico_processos': {
                'enabled': request.POST.get('widget_grafico_processos') == 'on',
                'order': 4
            },
            'atividades_recentes': {
                'enabled': request.POST.get('widget_atividades_recentes') == 'on',
                'order': 5
            },
            'clientes_ativos': {
                'enabled': request.POST.get('widget_clientes_ativos') == 'on',
                'order': 6
            },
        }
        
        preferencias.dashboard_widgets = dashboard_widgets
        preferencias.save()
        
        messages.success(request, 'Preferências atualizadas com sucesso!')
        return redirect('usuarios:preferencias')


def atualizar_preferencia_ajax(request):
    """View AJAX para atualizar preferências individuais"""
    if request.method == 'POST' and request.user.is_authenticated:
        preferencias = request.user.get_preferencias()
        
        campo = request.POST.get('campo')
        valor = request.POST.get('valor')
        
        try:
            if hasattr(preferencias, campo):
                # Converter valor para o tipo correto
                if campo in ['sidebar_collapsed', 'notificacoes_email', 'notificacoes_prazos', 
                           'notificacoes_sistema', 'notificacoes_marketing']:
                    valor = valor.lower() in ['true', '1', 'on']
                elif campo == 'items_por_pagina':
                    valor = int(valor)
                
                setattr(preferencias, campo, valor)
                preferencias.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Preferência atualizada com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Campo inválido'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao atualizar preferência: {str(e)}'
            })


class AlterarSenhaView(LoginRequiredMixin, TemplateView):
    """
    View para alterar a senha do usuário logado.
    Processa requisições POST com senha atual, nova senha e confirmação.
    """
    login_url = '/login/'
    
    def post(self, request, *args, **kwargs):
        """
        Processa a alteração de senha do usuário.
        Valida a senha atual e atualiza para a nova senha.
        """
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        # Validação da senha atual
        if not authenticate(username=request.user.username, password=senha_atual):
            messages.error(request, 'Senha atual incorreta.')
            return redirect('usuarios:perfil')
        
        # Validação das novas senhas
        if nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('usuarios:perfil')
        
        if len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            return redirect('usuarios:perfil')
        
        # Atualizar a senha
        try:
            request.user.set_password(nova_senha)
            request.user.save()
            
            # Manter o usuário logado após alterar a senha
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Senha alterada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao alterar senha: {str(e)}')
        
        return redirect('usuarios:perfil')
