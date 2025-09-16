from django.urls import path
from . import views

app_name = 'configuracoes'

urlpatterns = [
    # Dashboard
    path('', views.ConfiguracoesDashboardView.as_view(), name='dashboard'),
    
    # Tipos de Processo
    path('tipos-processo/', views.TipoProcessoListView.as_view(), name='tipos_processo'),
    path('tipos-processo/novo/', views.TipoProcessoCreateView.as_view(), name='criar_tipo_processo'),
    path('tipos-processo/<int:pk>/editar/', views.TipoProcessoUpdateView.as_view(), name='editar_tipo_processo'),
    path('tipos-processo/<int:pk>/excluir/', views.TipoProcessoDeleteView.as_view(), name='excluir_tipo_processo'),
    
    # Áreas do Direito
    path('areas-direito/', views.AreaDireitoListView.as_view(), name='areas_direito'),
    path('areas-direito/nova/', views.AreaDireitoCreateView.as_view(), name='criar_area_direito'),
    path('areas-direito/<int:pk>/editar/', views.AreaDireitoUpdateView.as_view(), name='editar_area_direito'),
    path('areas-direito/<int:pk>/excluir/', views.AreaDireitoDeleteView.as_view(), name='excluir_area_direito'),
    
    # Status de Processo
    path('status-processo/', views.StatusProcessoListView.as_view(), name='status_processo'),
    path('status-processo/novo/', views.StatusProcessoCreateView.as_view(), name='criar_status_processo'),
    path('status-processo/<int:pk>/editar/', views.StatusProcessoUpdateView.as_view(), name='editar_status_processo'),
    path('status-processo/<int:pk>/excluir/', views.StatusProcessoDeleteView.as_view(), name='excluir_status_processo'),
    
    # Modelos de Documento
    path('modelos-documentos/', views.ModeloDocumentoListView.as_view(), name='modelos_documentos'),
    path('modelos-documentos/novo/', views.ModeloDocumentoCreateView.as_view(), name='criar_modelo_documento'),
    path('modelos-documentos/<int:pk>/editar/', views.ModeloDocumentoUpdateView.as_view(), name='editar_modelo_documento'),
    path('modelos-documentos/<int:pk>/excluir/', views.ModeloDocumentoDeleteView.as_view(), name='excluir_modelo_documento'),
    
    # Configurações do Sistema
    path('sistema/', views.ConfiguracoesSistemaView.as_view(), name='sistema'),
    path('sistema/atualizar/', views.atualizar_configuracao, name='atualizar_configuracao'),
]