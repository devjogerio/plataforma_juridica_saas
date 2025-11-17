from django.urls import path

from .api_views import SaveDraftAPIView, LoadDraftAPIView, ClearDraftAPIView

urlpatterns = [
    path('drafts/save', SaveDraftAPIView.as_view(), name='drafts_save'),
    path('drafts/load', LoadDraftAPIView.as_view(), name='drafts_load'),
    path('drafts/clear', ClearDraftAPIView.as_view(), name='drafts_clear'),
]