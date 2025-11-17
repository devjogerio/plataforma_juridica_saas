from typing import Any, Dict

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .drafts import save_draft, load_draft, delete_draft


class SaveDraftAPIView(APIView):
    """Endpoint para salvar rascunho (checkpoint) de formulário"""
    permission_classes = [IsAuthenticated]
    

    def post(self, request, *args, **kwargs):
        body: Dict[str, Any] = request.data or {}
        form_slug = body.get('form_slug')
        object_id = body.get('object_id')
        payload = body.get('payload')

        if not form_slug or not isinstance(payload, dict):
            return Response({'detail': 'Parâmetros inválidos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ttl = getattr(settings, 'CHECKPOINT_TTL_SECONDS', 1200)
            data = save_draft(request.user, form_slug, object_id, payload, ttl)
            return Response({'ok': True, 'timestamp': data['timestamp']}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        except Exception:
            return Response({'detail': 'Erro ao salvar rascunho'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoadDraftAPIView(APIView):
    """Endpoint para carregar último rascunho salvo"""
    permission_classes = [IsAuthenticated]
    

    def get(self, request, *args, **kwargs):
        form_slug = request.query_params.get('form_slug')
        object_id = request.query_params.get('object_id')
        if not form_slug:
            return Response({'detail': 'Parâmetros inválidos'}, status=status.HTTP_400_BAD_REQUEST)

        data = load_draft(request.user, form_slug, object_id)
        if not data:
            return Response({'ok': False}, status=status.HTTP_204_NO_CONTENT)
        return Response({'ok': True, 'payload': data['payload'], 'timestamp': data['timestamp']}, status=status.HTTP_200_OK)


class ClearDraftAPIView(APIView):
    """Endpoint para limpar rascunho após submissão"""
    permission_classes = [IsAuthenticated]
    

    def delete(self, request, *args, **kwargs):
        form_slug = request.query_params.get('form_slug') or request.data.get('form_slug')
        object_id = request.query_params.get('object_id') or request.data.get('object_id')
        if not form_slug:
            return Response({'detail': 'Parâmetros inválidos'}, status=status.HTTP_400_BAD_REQUEST)
        removed = delete_draft(request.user, form_slug, object_id)
        return Response({'ok': bool(removed)}, status=status.HTTP_200_OK)