from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from processos.models import Processo, Andamento, Prazo
from clientes.models import Cliente
from financeiro.models import Honorario, Despesa
from usuarios.models import Usuario


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    View principal do Dashboard com KPIs, gráficos e informações importantes
    """
    template_name = 'core/dashboard.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Data atual para filtros
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # KPIs principais
        context['total_processos'] = Processo.objects.count()
        context['processos_ativos'] = Processo.objects.filter(status='ativo').count()
        context['processos_mes'] = Processo.objects.filter(
            data_inicio__gte=inicio_mes,
            data_inicio__lte=fim_mes
        ).count()
        context['total_clientes'] = Cliente.objects.count()
        
        # Processos por status para gráfico
        processos_por_status = list(
            Processo.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        context['processos_por_status'] = json.dumps(processos_por_status)
        
        # Prazos críticos (próximos 7 dias)
        proximos_7_dias = hoje + timedelta(days=7)
        context['prazos_criticos'] = Prazo.objects.filter(
            data_limite__gte=hoje,
            data_limite__lte=proximos_7_dias,
            cumprido=False
        ).select_related('processo').order_by('data_limite')[:10]
        
        # Últimos andamentos
        context['ultimos_andamentos'] = Andamento.objects.select_related(
            'processo', 'usuario'
        ).order_by('-data_andamento')[:5]
        
        # Estatísticas financeiras
        context['total_honorarios'] = Honorario.objects.aggregate(
            total=Sum('valor_total')
        )['total'] or 0
        
        context['total_despesas'] = Despesa.objects.aggregate(
            total=Sum('valor')
        )['total'] or 0
        
        # Processos por área do direito
        processos_por_area = list(
            Processo.objects.values('area_direito')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        context['processos_por_area'] = json.dumps(processos_por_area)
        
        return context


class LoginView(DjangoLoginView):
    """
    View customizada para login
    """
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/'


class LogoutView(DjangoLogoutView):
    """
    View customizada para logout
    """
    next_page = '/login/'
