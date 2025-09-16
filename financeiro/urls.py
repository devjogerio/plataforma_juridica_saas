from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Dashboard
    path('', views.FinanceiroDashboardView.as_view(), name='dashboard'),
    
    # Transações
    path('transacoes/', views.transacoes_view, name='transacoes'),
    
    # Honorários
    path('honorarios/', views.HonorarioListView.as_view(), name='honorarios'),
    path('honorarios/novo/', views.HonorarioCreateView.as_view(), name='criar_honorario'),
    path('honorarios/<uuid:pk>/', views.HonorarioDetailView.as_view(), name='detalhe_honorario'),
    path('honorarios/<uuid:pk>/editar/', views.HonorarioUpdateView.as_view(), name='editar_honorario'),
    
    # Parcelas de Honorários
    path('parcelas/<uuid:pk>/pagar/', views.marcar_parcela_paga, name='marcar_parcela_paga'),
    
    # Despesas
    path('despesas/', views.DespesaListView.as_view(), name='despesas'),
    path('despesas/nova/', views.DespesaCreateView.as_view(), name='criar_despesa'),
    path('despesas/<uuid:pk>/', views.DespesaDetailView.as_view(), name='detalhe_despesa'),
    path('despesas/<uuid:pk>/editar/', views.DespesaUpdateView.as_view(), name='editar_despesa'),
    path('despesas/<uuid:pk>/reembolsar/', views.marcar_despesa_reembolsada, name='marcar_despesa_reembolsada'),
    
    # Contas Bancárias
    path('contas/', views.ContaBancariaListView.as_view(), name='contas_bancarias'),
    path('contas/nova/', views.ContaBancariaCreateView.as_view(), name='criar_conta_bancaria'),
    path('contas/<uuid:pk>/editar/', views.ContaBancariaUpdateView.as_view(), name='editar_conta_bancaria'),
    
    # Relatórios
    path('relatorios/', views.RelatoriosFinanceirosView.as_view(), name='relatorios'),
    path('relatorios/exportar/', views.exportar_relatorio_financeiro, name='exportar_relatorio'),
    
    # APIs
    path('api/estatisticas/', views.estatisticas_financeiras, name='api_estatisticas'),
]