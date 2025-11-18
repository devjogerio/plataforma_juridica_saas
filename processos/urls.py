from django.urls import path
from . import views

app_name = 'processos'

urlpatterns = [
    path('', views.ProcessoListView.as_view(), name='lista'),
    path('list/', views.ProcessoListView.as_view(), name='list'),
    path('novo/', views.ProcessoCreateView.as_view(), name='criar'),
    path('primeiro/', views.ProcessoPrimeiroCreateView.as_view(), name='primeiro_processo'),
    path('<uuid:pk>/', views.ProcessoDetailView.as_view(), name='detalhe'),
    path('<uuid:pk>/editar/', views.ProcessoUpdateView.as_view(), name='editar'),
    path('<uuid:pk>/excluir/', views.ProcessoDeleteView.as_view(), name='excluir'),
    path('<uuid:pk>/andamentos/', views.AndamentoListView.as_view(), name='andamentos'),
    path('<uuid:pk>/andamentos/novo/', views.AndamentoCreateView.as_view(), name='criar_andamento'),
    path('<uuid:pk>/prazos/', views.PrazoListView.as_view(), name='prazos'),
    path('<uuid:pk>/prazos/novo/', views.PrazoCreateView.as_view(), name='criar_prazo'),
    path('prazos/<uuid:pk>/cumprir/', views.CumprirPrazoView.as_view(), name='cumprir_prazo'),
    path('prazos/', views.PrazosGeraisListView.as_view(), name='prazos'),
    path('prazos/vencendo/', views.PrazosVencendoView.as_view(), name='prazos_vencendo'),
]
