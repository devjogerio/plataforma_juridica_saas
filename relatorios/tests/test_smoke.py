import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_urlconf_relatorios_carrega(client, settings):
    settings.LOGIN_URL = '/login/'
    # Apenas verificar que a homepage de relatórios resolve para não autenticado (redireciona)
    resp = client.get('/relatorios/')
    assert resp.status_code in (301, 302, 200)


@pytest.mark.django_db
def test_views_relatorios_autenticado_request_factory():
    from django.test import RequestFactory
    from relatorios.views import RelatoriosDashboardView, ListaFiltrosView, ListaTemplatesView

    User = get_user_model()
    user = User.objects.create_user(username='u', password='p')
    rf = RequestFactory()

    # Dashboard
    req = rf.get('/relatorios/')
    req.user = user
    resp = RelatoriosDashboardView.as_view()(req)
    assert resp.status_code == 200

    # Lista de filtros
    req2 = rf.get(reverse('relatorios:lista_filtros'))
    req2.user = user
    resp2 = ListaFiltrosView.as_view()(req2)
    assert resp2.status_code == 200

    # Templates
    req3 = rf.get(reverse('relatorios:lista_templates'))
    req3.user = user
    resp3 = ListaTemplatesView.as_view()(req3)
    assert resp3.status_code == 200