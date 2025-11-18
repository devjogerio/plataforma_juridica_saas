from django.urls import path, include
from django.views.generic import RedirectView
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard principal
    path('', views.RelatoriosDashboardView.as_view(), name='dashboard'),
    
    # Relatórios básicos
    path('processos/', views.RelatorioProcessosView.as_view(), name='relatorio_processos'),
    path('clientes/excel/', views.ClientesExcelExportView.as_view(), name='clientes_excel'),
    
    # Filtros Avançados
    path('filtros/', views.ListaFiltrosView.as_view(), name='lista_filtros'),
    path('filtros/criar/', views.CriarFiltroView.as_view(), name='criar_filtro'),
    path('filtros/<uuid:pk>/editar/', views.EditarFiltroView.as_view(), name='editar_filtro'),
    path('filtros/<uuid:pk>/excluir/', views.ExcluirFiltroView.as_view(), name='excluir_filtro'),
    path('filtros/<uuid:pk>/', views.VisualizarFiltroView.as_view(), name='detalhe_filtro'),
    path('filtros/<uuid:pk>/testar/', views.TestarFiltroView.as_view(), name='testar_filtro'),
    
    # Templates de Relatório
    path('templates/', views.ListaTemplatesView.as_view(), name='lista_templates'),
    path('templates/criar/', views.CriarTemplateView.as_view(), name='criar_template'),
    path('templates/<uuid:pk>/editar/', views.EditarTemplateView.as_view(), name='editar_template'),
    
    # Execução de Relatórios
    path('executar/', views.ExecutarRelatorioView.as_view(), name='executar_relatorio'),
    path('execucoes/', views.ListaExecucoesView.as_view(), name='execucoes'),
    
    # APIs
    path('api/campos-filtro/', views.APIObterCamposFiltroView.as_view(), name='api_campos_filtro'),
    path('api/testar-filtro/', views.APITestarConfiguracaoFiltroView.as_view(), name='api_testar_filtro'),
    
    # URLs legadas (mantidas para compatibilidade)
    path('clientes/', RedirectView.as_view(pattern_name='relatorios:dashboard'), name='clientes'),
    path('financeiro/', RedirectView.as_view(pattern_name='relatorios:dashboard'), name='financeiro'),
    path('produtividade/', RedirectView.as_view(pattern_name='relatorios:dashboard'), name='produtividade'),
    path('dashboards/', RedirectView.as_view(pattern_name='relatorios:dashboard'), name='dashboards'),
]
