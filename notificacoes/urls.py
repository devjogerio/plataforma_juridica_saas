from django.urls import path
from . import views

app_name = 'notificacoes'

urlpatterns = [
    # Dashboard de notificações
    path('', views.dashboard_notificacoes, name='dashboard'),
    
    # Lista de notificações
    path('lista/', views.NotificacaoListView.as_view(), name='lista'),
    
    # Ações com notificações
    path('marcar-lida/<int:notificacao_id>/', views.marcar_como_lida, name='marcar_lida'),
    path('marcar-nao-lida/<int:notificacao_id>/', views.marcar_como_nao_lida, name='marcar_nao_lida'),
    path('marcar-todas-lidas/', views.marcar_todas_como_lidas, name='marcar_todas_lidas'),
    path('excluir/<int:notificacao_id>/', views.excluir_notificacao, name='excluir'),
    path('excluir-multiplas/', views.excluir_multiplas_notificacoes, name='excluir_multiplas'),
    path('limpar-lidas/', views.limpar_lidas, name='limpar_lidas'),
    
    # AJAX endpoints
    path('ajax/recentes/', views.notificacoes_recentes_ajax, name='recentes_ajax'),
    
    # Configurações
    path('configuracoes/', views.ConfiguracaoNotificacaoUpdateView.as_view(), name='configuracoes'),
]