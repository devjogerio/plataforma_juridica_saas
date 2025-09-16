from django.urls import path
from . import views

app_name = 'alertas'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_alertas, name='dashboard'),
    
    # Listagem e CRUD
    path('lista/', views.AlertaListView.as_view(), name='lista'),
    path('novo/', views.AlertaCreateView.as_view(), name='novo'),
    path('<uuid:pk>/editar/', views.AlertaUpdateView.as_view(), name='editar'),
    path('<uuid:pk>/excluir/', views.AlertaDeleteView.as_view(), name='excluir'),
    
    # Ações individuais
    path('<uuid:alerta_id>/concluir/', views.marcar_como_concluido, name='concluir'),
    path('<uuid:alerta_id>/adiar/', views.adiar_alerta, name='adiar'),
    path('<uuid:alerta_id>/cancelar/', views.cancelar_alerta, name='cancelar'),
    
    # Ações em lote
    path('acao-lote/', views.acao_lote, name='acao_lote'),
    
    # Configurações
    path('configuracoes/', views.ConfiguracaoAlertaUpdateView.as_view(), name='configuracoes'),
    
    # API endpoints
    path('api/proximos/', views.api_alertas_proximos, name='api_proximos'),
]