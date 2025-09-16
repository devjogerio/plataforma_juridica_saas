"""
Testes unitários para o módulo de processos
"""
import pytest
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from processos.models import Processo, Andamento, Prazo
from documentos.models import Documento
from configuracoes.models import TipoProcesso
# from processos.forms import ProcessoForm, AndamentoForm  # Forms não existem no módulo processos
from tests.factories import (
    ProcessoFactory, AndamentoFactory, PrazoFactory, DocumentoFactory,
    ClienteFactory, UserFactory
)

User = get_user_model()


@pytest.mark.django_db
class TestProcessoModel:
    """Testes para o modelo Processo"""
    
    def test_criar_processo_valido(self):
        """Testa criação de processo com dados válidos"""
        processo = ProcessoFactory()
        assert processo.pk is not None
        assert processo.ativo is True
        assert processo.created_at is not None
    
    def test_processo_str_representation(self):
        """Testa representação string do processo"""
        processo = ProcessoFactory(numero_processo="1234567-89.2023.8.26.0001")
        assert str(processo) == "1234567-89.2023.8.26.0001"
    
    def test_processo_com_cliente(self):
        """Testa processo com cliente associado"""
        cliente = ClienteFactory()
        processo = ProcessoFactory(cliente=cliente)
        assert processo.cliente == cliente
    
    def test_processo_com_tipo(self):
        """Testa processo com tipo associado"""
        processo = ProcessoFactory(tipo_processo="judicial")
        assert processo.tipo_processo == "judicial"
    
    def test_processo_com_tribunal(self):
        """Testa processo com comarca/tribunal"""
        processo = ProcessoFactory(comarca_tribunal="TJSP")
        assert processo.comarca_tribunal == "TJSP"
    
    def test_processo_valor_causa(self):
        """Testa valor da causa do processo"""
        processo = ProcessoFactory(valor_causa=10000.50)
        assert processo.valor_causa == 10000.50
    
    def test_processo_status_choices(self):
        """Testa status válidos do processo"""
        status_validos = ['ativo', 'arquivado', 'suspenso', 'finalizado']
        
        for status in status_validos:
            processo = ProcessoFactory(status=status)
            assert processo.status == status
    
    def test_processo_inativo(self):
        """Testa processo com status inativo"""
        processo = ProcessoFactory(status='arquivado')
        assert processo.status == 'arquivado'
    
    def test_validacao_numero_processo(self):
        """Testa validação do número do processo"""
        # Número inválido
        processo = ProcessoFactory.build(numero_processo="123")
        with pytest.raises(ValidationError):
            processo.full_clean()
    
    def test_unique_numero_processo(self):
        """Testa unicidade do número do processo"""
        numero = "1234567-89.2023.8.26.0001"
        ProcessoFactory(numero_processo=numero)
        
        with pytest.raises(Exception):  # IntegrityError
            ProcessoFactory(numero_processo=numero)


@pytest.mark.django_db
class TestAndamentoModel:
    """Testes para o modelo Andamento"""
    
    def test_criar_andamento(self):
        """Testa criação de andamento"""
        andamento = AndamentoFactory()
        assert andamento.pk is not None
        assert andamento.processo is not None
        assert andamento.usuario is not None
    
    def test_andamento_str(self):
        """Testa representação string do andamento"""
        andamento = AndamentoFactory(
            tipo_andamento="Petição",
            descricao="Petição inicial protocolada"
        )
        expected = f"Petição - {andamento.processo.numero_processo}"
        assert str(andamento) == expected
    
    def test_andamento_data_automatica(self):
        """Testa data automática do andamento"""
        andamento = AndamentoFactory()
        assert andamento.data_andamento is not None
        assert andamento.data_andamento <= date.today()
    
    def test_tipos_andamento_validos(self):
        """Testa tipos de andamento válidos"""
        tipos_validos = ['peticao', 'audiencia', 'sentenca', 'recurso', 'outros']
        
        for tipo in tipos_validos:
            andamento = AndamentoFactory(tipo_andamento=tipo)
            assert andamento.tipo_andamento == tipo


@pytest.mark.django_db
class TestPrazoModel:
    """Testes para o modelo Prazo"""
    
    def test_criar_prazo(self):
        """Testa criação de prazo"""
        prazo = PrazoFactory()
        assert prazo.pk is not None
        assert prazo.processo is not None
        assert prazo.data_vencimento is not None
    
    def test_prazo_str(self):
        """Testa representação string do prazo"""
        prazo = PrazoFactory(
            descricao="Contestação",
            data_vencimento=date.today() + timedelta(days=15)
        )
        expected = f"Contestação - {prazo.data_vencimento.strftime('%d/%m/%Y')}"
        assert str(prazo) == expected
    
    def test_prazo_vencido(self):
        """Testa identificação de prazo vencido"""
        prazo_vencido = PrazoFactory(
            data_vencimento=date.today() - timedelta(days=1)
        )
        prazo_futuro = PrazoFactory(
            data_vencimento=date.today() + timedelta(days=1)
        )
        
        # Método para verificar se está vencido (implementar no modelo)
        assert prazo_vencido.data_vencimento < date.today()
        assert prazo_futuro.data_vencimento > date.today()
    
    def test_prazo_cumprido(self):
        """Testa prazo cumprido"""
        prazo = PrazoFactory(cumprido=True)
        assert prazo.cumprido is True
    
    def test_prazo_com_responsavel(self):
        """Testa prazo com usuário responsável"""
        usuario = UserFactory()
        prazo = PrazoFactory(usuario_responsavel=usuario)
        assert prazo.usuario_responsavel == usuario


@pytest.mark.django_db
class TestDocumentoModel:
    """Testes para o modelo Documento"""
    
    def test_criar_documento(self):
        """Testa criação de documento"""
        documento = DocumentoFactory()
        assert documento.pk is not None
        assert documento.processo is not None
        assert documento.nome is not None
    
    def test_documento_str(self):
        """Testa representação string do documento"""
        documento = DocumentoFactory(nome="Petição Inicial")
        expected = f"Petição Inicial - {documento.processo.numero_processo}"
        assert str(documento) == expected
    
    def test_documento_com_arquivo(self):
        """Testa documento com arquivo"""
        documento = DocumentoFactory(arquivo="documentos/peticao.pdf")
        assert "peticao.pdf" in documento.arquivo.name
    
    def test_tipos_documento_validos(self):
        """Testa tipos de documento válidos"""
        tipos_validos = ['peticao', 'contrato', 'procuracao', 'certidao', 'outros']
        
        for tipo in tipos_validos:
            documento = DocumentoFactory(tipo_documento=tipo)
            assert documento.tipo_documento == tipo


class TestProcessoViews(TestCase):
    """Testes para views de processos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = UserFactory()
        self.cliente = ClienteFactory()
        self.processo = ProcessoFactory(cliente=self.cliente)
    
    def test_lista_processos_requer_login(self):
        """Testa que listagem requer autenticação"""
        url = reverse('processos:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect para login
    
    def test_lista_processos_autenticado(self):
        """Testa listagem com usuário autenticado"""
        self.client.force_login(self.user)
        url = reverse('processos:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_detalhe_processo(self):
        """Testa visualização de detalhes do processo"""
        self.client.force_login(self.user)
        url = reverse('processos:detalhe', kwargs={'pk': self.processo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.processo.numero_processo)
    
    def test_criar_processo_get(self):
        """Testa exibição do formulário de criação"""
        self.client.force_login(self.user)
        url = reverse('processos:criar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_criar_processo_post_valido(self):
        """Testa criação de processo com dados válidos"""
        self.client.force_login(self.user)
        tipo_processo = TipoProcessoFactory()
        tribunal = TribunalFactory()
        
        url = reverse('processos:criar')
        data = {
            'numero_processo': '9876543-21.2023.8.26.0100',
            'cliente': self.cliente.pk,
            'tipo_processo': tipo_processo.pk,
            'tribunal': tribunal.pk,
            'assunto': 'Processo de teste',
            'valor_causa': '5000.00',
            'status': 'ativo',
            'data_distribuicao': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso
        
        # Verifica se processo foi criado
        self.assertTrue(
            Processo.objects.filter(numero_processo='9876543-21.2023.8.26.0100').exists()
        )
    
    def test_editar_processo(self):
        """Testa edição de processo"""
        self.client.force_login(self.user)
        url = reverse('processos:editar', kwargs={'pk': self.processo.pk})
        
        data = {
            'numero_processo': self.processo.numero_processo,
            'cliente': self.processo.cliente.pk,
            'tipo_processo': self.processo.tipo_processo.pk,
            'tribunal': self.processo.tribunal.pk,
            'assunto': 'Processo editado',
            'valor_causa': str(self.processo.valor_causa or '0'),
            'status': self.processo.status,
            'data_distribuicao': self.processo.data_distribuicao.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verifica se foi editado
        self.processo.refresh_from_db()
        self.assertEqual(self.processo.assunto, 'Processo editado')
    
    def test_busca_processos(self):
        """Testa busca de processos"""
        self.client.force_login(self.user)
        
        # Criar processo com número específico
        ProcessoFactory(numero_processo='1111111-11.2023.8.26.0001')
        
        url = reverse('processos:lista')
        response = self.client.get(url, {'q': '1111111'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1111111-11.2023.8.26.0001')
    
    def test_filtro_por_status(self):
        """Testa filtro por status"""
        self.client.force_login(self.user)
        
        # Criar processos com status diferentes
        ProcessoFactory(status='ativo')
        ProcessoFactory(status='arquivado')
        
        url = reverse('processos:lista')
        response = self.client.get(url, {'status': 'ativo'})
        
        self.assertEqual(response.status_code, 200)
    
    def test_filtro_por_cliente(self):
        """Testa filtro por cliente"""
        self.client.force_login(self.user)
        
        cliente_especifico = ClienteFactory(nome_razao_social='Cliente Específico')
        ProcessoFactory(cliente=cliente_especifico)
        
        url = reverse('processos:lista')
        response = self.client.get(url, {'cliente': cliente_especifico.pk})
        
        self.assertEqual(response.status_code, 200)


class TestAndamentoViews(TestCase):
    """Testes para views de andamentos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = UserFactory()
        self.processo = ProcessoFactory()
        self.andamento = AndamentoFactory(processo=self.processo)
    
    def test_lista_andamentos(self):
        """Testa listagem de andamentos"""
        self.client.force_login(self.user)
        url = reverse('processos:andamentos', kwargs={'pk': self.processo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_criar_andamento(self):
        """Testa criação de andamento"""
        self.client.force_login(self.user)
        url = reverse('processos:criar_andamento', kwargs={'pk': self.processo.pk})
        
        data = {
            'tipo_andamento': 'peticao',
            'descricao': 'Novo andamento',
            'data_andamento': date.today().strftime('%Y-%m-%d'),
            'observacoes': 'Observações do andamento'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verifica se foi criado
        self.assertTrue(
            Andamento.objects.filter(
                processo=self.processo,
                descricao='Novo andamento'
            ).exists()
        )


class TestPrazoViews(TestCase):
    """Testes para views de prazos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = UserFactory()
        self.processo = ProcessoFactory()
        self.prazo = PrazoFactory(processo=self.processo)
    
    def test_lista_prazos(self):
        """Testa listagem de prazos"""
        self.client.force_login(self.user)
        url = reverse('processos:prazos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_prazos_vencendo(self):
        """Testa listagem de prazos vencendo"""
        self.client.force_login(self.user)
        
        # Criar prazo vencendo em 3 dias
        PrazoFactory(
            data_vencimento=date.today() + timedelta(days=3),
            cumprido=False
        )
        
        url = reverse('processos:prazos_vencendo')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_marcar_prazo_cumprido(self):
        """Testa marcar prazo como cumprido"""
        self.client.force_login(self.user)
        url = reverse('processos:cumprir_prazo', kwargs={'pk': self.prazo.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Verifica se foi marcado como cumprido
        self.prazo.refresh_from_db()
        self.assertTrue(self.prazo.cumprido)


# class TestProcessoForms(TestCase):
#     """Testes para formulários de processos"""
#     
#     def test_processo_form_valido(self):
#         """Testa formulário com dados válidos"""
#         cliente = ClienteFactory()
#         tipo_processo = TipoProcessoFactory()
#         tribunal = TribunalFactory()
#         
#         form_data = {
#             'numero_processo': '1234567-89.2023.8.26.0001',
#             'cliente': cliente.pk,
#             'tipo_processo': tipo_processo.pk,
#             'tribunal': tribunal.pk,
#             'assunto': 'Processo teste',
#             'valor_causa': '1000.00',
#             'status': 'ativo',
#             'data_distribuicao': date.today()
#         }
#         
#         form = ProcessoForm(data=form_data)
#         self.assertTrue(form.is_valid())
#     
#     def test_processo_form_numero_invalido(self):
#         """Testa formulário com número inválido"""
#         form_data = {
#             'numero_processo': '123',  # Número inválido
#             'cliente': ClienteFactory().pk,
#             'tipo_processo': TipoProcessoFactory().pk,
#             'tribunal': TribunalFactory().pk,
#             'assunto': 'Processo teste'
#         }
#         
#         form = ProcessoForm(data=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertIn('numero_processo', form.errors)
#     
#     def test_andamento_form_valido(self):
#         """Testa formulário de andamento válido"""
#         form_data = {
#             'tipo_andamento': 'peticao',
#             'descricao': 'Andamento teste',
#             'data_andamento': date.today(),
#             'observacoes': 'Observações'
#         }
#         
#         form = AndamentoForm(data=form_data)
#         self.assertTrue(form.is_valid())


class TestProcessoAPI(APITestCase):
    """Testes para API de processos"""
    
    def setUp(self):
        """Configuração inicial dos testes de API"""
        self.user = UserFactory()
        self.processo = ProcessoFactory()
    
    def test_lista_processos_api_sem_auth(self):
        """Testa API sem autenticação"""
        url = reverse('api:processos-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_lista_processos_api_com_auth(self):
        """Testa API com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:processos-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_criar_processo_api(self):
        """Testa criação via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:processos-list')
        
        data = {
            'numero_processo': '9999999-99.2023.8.26.0001',
            'cliente': ClienteFactory().pk,
            'tipo_processo': TipoProcessoFactory().pk,
            'tribunal': TribunalFactory().pk,
            'assunto': 'Processo API',
            'status': 'ativo'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_filtros_api(self):
        """Testa filtros na API"""
        self.client.force_authenticate(user=self.user)
        
        cliente = ClienteFactory()
        ProcessoFactory(cliente=cliente, status='ativo')
        ProcessoFactory(status='arquivado')
        
        # Filtro por cliente
        url = reverse('api:processos-list')
        response = self.client.get(url, {'cliente': cliente.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filtro por status
        response = self.client.get(url, {'status': 'ativo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.integration
class TestProcessoIntegration:
    """Testes de integração para processos"""
    
    @pytest.mark.django_db
    def test_fluxo_completo_processo(self, authenticated_client):
        """Testa fluxo completo do processo"""
        client = authenticated_client
        cliente = ClienteFactory()
        tipo_processo = TipoProcessoFactory()
        tribunal = TribunalFactory()
        
        # 1. Criar processo
        create_url = reverse('processos:criar')
        data = {
            'numero_processo': '5555555-55.2023.8.26.0001',
            'cliente': cliente.pk,
            'tipo_processo': tipo_processo.pk,
            'tribunal': tribunal.pk,
            'assunto': 'Processo integração',
            'status': 'ativo',
            'data_distribuicao': date.today().strftime('%Y-%m-%d')
        }
        
        response = client.post(create_url, data)
        assert response.status_code == 302
        
        # 2. Buscar processo criado
        processo = Processo.objects.get(numero_processo='5555555-55.2023.8.26.0001')
        
        # 3. Adicionar andamento
        andamento_url = reverse('processos:criar_andamento', kwargs={'pk': processo.pk})
        andamento_data = {
            'tipo_andamento': 'peticao',
            'descricao': 'Petição inicial',
            'data_andamento': date.today().strftime('%Y-%m-%d')
        }
        
        response = client.post(andamento_url, andamento_data)
        assert response.status_code == 302
        
        # 4. Adicionar prazo
        prazo_url = reverse('processos:criar_prazo', kwargs={'pk': processo.pk})
        prazo_data = {
            'descricao': 'Contestação',
            'data_vencimento': (date.today() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'tipo_prazo': 'contestacao'
        }
        
        response = client.post(prazo_url, prazo_data)
        assert response.status_code == 302
        
        # 5. Verificar na página de detalhes
        detail_url = reverse('processos:detalhe', kwargs={'pk': processo.pk})
        response = client.get(detail_url)
        assert response.status_code == 200
        
        # Verificar se andamento e prazo aparecem
        assert 'Petição inicial' in response.content.decode()
        assert 'Contestação' in response.content.decode()
    
    @pytest.mark.django_db
    def test_processo_com_documentos(self, authenticated_client):
        """Testa processo com documentos"""
        client = authenticated_client
        processo = ProcessoFactory()
        
        # Criar documentos
        DocumentoFactory.create_batch(3, processo=processo)
        
        # Verificar na página de detalhes
        url = reverse('processos:detalhe', kwargs={'pk': processo.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'documentos' in response.context
        assert response.context['processo'].documentos.count() == 3


@pytest.mark.slow
class TestProcessoPerformance:
    """Testes de performance para processos"""
    
    @pytest.mark.django_db
    def test_listagem_com_muitos_processos(self, authenticated_client):
        """Testa performance da listagem com muitos processos"""
        import time
        
        # Criar muitos processos
        ProcessoFactory.create_batch(50)
        
        url = reverse('processos:lista')
        
        start_time = time.time()
        response = authenticated_client.get(url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Deve ser rápido (< 3s)
    
    @pytest.mark.django_db
    def test_queries_otimizadas_detalhes(self, authenticated_client):
        """Testa queries otimizadas na página de detalhes"""
        from django.test.utils import override_settings
        from django.db import connection
        
        processo = ProcessoFactory()
        AndamentoFactory.create_batch(5, processo=processo)
        PrazoFactory.create_batch(3, processo=processo)
        DocumentoFactory.create_batch(2, processo=processo)
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            url = reverse('processos:detalhe', kwargs={'pk': processo.pk})
            response = authenticated_client.get(url)
            
            assert response.status_code == 200
            # Deve usar poucas queries devido às otimizações
            assert len(connection.queries) < 15