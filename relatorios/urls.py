from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard principal
    path('', views.RelatoriosDashboardView.as_view(), name='dashboard'),
    
    # Relatórios específicos
    path('processos/', views.RelatorioProcessosView.as_view(), name='processos'),
    path('clientes/', views.RelatorioClientesView.as_view(), name='clientes'),
    path('financeiro/', views.RelatorioFinanceiroView.as_view(), name='financeiro'),
    path('produtividade/', views.RelatorioProdutividadeView.as_view(), name='produtividade'),
    
    # Templates de relatórios
    path('templates/', views.TemplateRelatorioListView.as_view(), name='templates'),
    path('templates/criar/', views.TemplateRelatorioCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/editar/', views.TemplateRelatorioUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/excluir/', views.TemplateRelatorioDeleteView.as_view(), name='template_delete'),
    
    # Dashboards personalizados
    path('dashboards/', views.DashboardPersonalizadoListView.as_view(), name='dashboards'),
    path('dashboards/criar/', views.DashboardPersonalizadoCreateView.as_view(), name='dashboard_create'),
    path('dashboards/<int:pk>/', views.DashboardPersonalizadoDetailView.as_view(), name='dashboard_detail'),
    
    # Execução de relatórios
    path('executar/<int:template_id>/', views.executar_relatorio, name='executar'),
    
    # Exportação
    path('exportar/<int:execucao_id>/', views.exportar_relatorio, name='exportar'),
]