from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Listagem e busca
    path('', views.lista_clientes, name='lista'),
    
    # CRUD de clientes
    path('cadastrar/', views.criar_cliente, name='cadastrar'),
    path('<uuid:pk>/', views.detalhe_cliente, name='detalhe'),
    path('<uuid:pk>/editar/', views.editar_cliente, name='editar'),
    
    # Interações
    path('<uuid:cliente_id>/interacao/', views.adicionar_interacao, name='adicionar_interacao'),
    
    # AJAX endpoints
    path('<uuid:cliente_id>/toggle-ativo/', views.toggle_ativo_cliente, name='toggle_ativo'),
    path('buscar/', views.buscar_clientes_ajax, name='buscar_ajax'),
]