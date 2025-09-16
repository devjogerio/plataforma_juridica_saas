from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.UsuarioListView.as_view(), name='lista'),
    path('novo/', views.UsuarioCreateView.as_view(), name='criar'),
    path('<uuid:pk>/', views.UsuarioDetailView.as_view(), name='detalhe'),
    path('<uuid:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('perfil/editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),
    path('perfil/alterar-senha/', views.AlterarSenhaView.as_view(), name='alterar_senha'),
    path('preferencias/', views.PreferenciasView.as_view(), name='preferencias'),
    path('preferencias/ajax/', views.atualizar_preferencia_ajax, name='atualizar_preferencia_ajax'),
    path('permissoes/', views.PermissoesView.as_view(), name='permissoes'),
    path('<uuid:pk>/permissoes/', views.UsuarioPermissoesView.as_view(), name='usuario_permissoes'),
]