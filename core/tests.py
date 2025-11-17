from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate

from .drafts import save_draft, load_draft, delete_draft


class DraftsServiceTests(TestCase):
    """Testes do serviço de rascunhos"""

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_save_and_load_draft(self):
        User = get_user_model()
        user = User.objects.create_user(username='u1', password='p')
        payload = {'data': {'campo': 'valor'}, 'schemaVersion': 1}
        data = save_draft(user, 'processos_form', None, payload)
        self.assertIn('timestamp', data)
        loaded = load_draft(user, 'processos_form', None)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['payload']['data']['campo'], 'valor')

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_delete_draft(self):
        User = get_user_model()
        user = User.objects.create_user(username='u2', password='p')
        payload = {'data': {'a': 1}}
        save_draft(user, 'processos_form', '1', payload)
        removed = delete_draft(user, 'processos_form', '1')
        self.assertTrue(removed)
        self.assertIsNone(load_draft(user, 'processos_form', '1'))


class DraftsAPITests(TestCase):
    """Testes dos endpoints de rascunhos"""

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='api', password='p')
        self.factory = APIRequestFactory()

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_save_and_load_via_api(self):
        from core.api_views import SaveDraftAPIView, LoadDraftAPIView
        req = self.factory.post('/api/v1/forms/drafts/save', {
            'form_slug': 'processos_form',
            'object_id': '',
            'payload': {'data': {'campo': 'valor'}, 'schemaVersion': 1}
        }, format='json')
        force_authenticate(req, user=self.user)
        resp = SaveDraftAPIView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

        req2 = self.factory.get('/api/v1/forms/drafts/load', {'form_slug': 'processos_form', 'object_id': ''})
        force_authenticate(req2, user=self.user)
        resp2 = LoadDraftAPIView.as_view()(req2)
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.data['ok'])
        self.assertEqual(resp2.data['payload']['data']['campo'], 'valor')

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_clear_via_api(self):
        from core.api_views import SaveDraftAPIView, ClearDraftAPIView
        req = self.factory.post('/api/v1/forms/drafts/save', {
            'form_slug': 'processos_form',
            'object_id': '123',
            'payload': {'data': {'x': 'y'}}
        }, format='json')
        force_authenticate(req, user=self.user)
        SaveDraftAPIView.as_view()(req)

        req2 = self.factory.delete('/api/v1/forms/drafts/clear', {'form_slug': 'processos_form', 'object_id': '123'})
        force_authenticate(req2, user=self.user)
        resp = ClearDraftAPIView.as_view()(req2)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['ok'])

# Create your tests here.
