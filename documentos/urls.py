from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.DocumentoListView.as_view(), name='lista'),
    path('upload/', views.DocumentoUploadView.as_view(), name='upload'),
    path('<uuid:pk>/', views.DocumentoDetailView.as_view(), name='detalhe'),
    path('<uuid:pk>/download/', views.DocumentoDownloadView.as_view(), name='download'),
    path('<uuid:pk>/excluir/', views.DocumentoDeleteView.as_view(), name='excluir'),
    path('processo/<uuid:processo_id>/', views.DocumentosProcessoView.as_view(), name='processo'),
]