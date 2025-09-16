"""
Testes unitários para o módulo de clientes
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente, InteracaoCliente
from clientes.forms import ClienteForm
from tests.factories import ClienteFactory, UserFactory, InteracaoClienteFactory

User = get_user_model()


@pytest.mark.django_db
class TestClienteModel:
    """Testes para o modelo Cliente"""
    
    def test_criar_cliente_valido(self):
        """Testa criação de cliente com dados válidos"""
        cliente = ClienteFactory()
        assert cliente.pk is not None
        assert cliente.ativo is True
        assert cliente.created_at is not None
    
    def test_cliente_str_representation(self):
        """Testa representação string do cliente"""
        cliente = ClienteFactory(nome_razao_social="João Silva")
        assert str(cliente) == "João Silva"
    
    def test_cliente_pessoa_fisica(self):
        """Testa criação de cliente pessoa física"""
        cliente = ClienteFactory(pessoa_fisica=True)
        assert cliente.tipo_pessoa == 'PF'
        assert len(cliente.cpf_cnpj) == 11  # CPF tem 11 dígitos
    
    def test_cliente_pessoa_juridica(self):
        """Testa criação de cliente pessoa jurídica"""
        cliente = ClienteFactory(pessoa_juridica=True)
        assert cliente.tipo_pessoa == 'PJ'
        assert len(cliente.cpf_cnpj) == 14  # CNPJ tem 14 dígitos
    
    def test_cliente_inativo(self):
        """Testa cliente inativo"""
        cliente = ClienteFactory(inativo=True)
        assert cliente.ativo is False
    
    def test_validacao_email(self):
        """Testa validação de email"""
        cliente = ClienteFactory.build(email="email_invalido")
        with pytest.raises(ValidationError):
            cliente.full_clean()
    
    def test_unique_cpf_cnpj(self):
        """Testa unicidade de CPF/CNPJ"""
        cpf = "12345678901"
        ClienteFactory(cpf_cnpj=cpf)
        
        with pytest.raises(Exception):  # IntegrityError
            ClienteFactory(cpf_cnpj=cpf)
    
    def test_cliente_com_processos(self, cliente_com_processos):
        """Testa cliente com processos relacionados"""
        assert cliente_com_processos.processos.count() == 3
    
    def test_soft_delete(self):
        """Testa exclusão lógica do cliente"""
        cliente = ClienteFactory()
        cliente.ativo = False
        cliente.save()
        
        assert Cliente.objects.filter(pk=cliente.pk).exists()
        assert not Cliente.objects.filter(pk=cliente.pk, ativo=True).exists()


@pytest.mark.django_db
class TestInteracaoClienteModel:
    """Testes para o modelo InteracaoCliente"""
    
    def test_criar_interacao(self):
        """Testa criação de interação"""
        interacao = InteracaoClienteFactory()
        assert interacao.pk is not None
        assert interacao.cliente is not None
        assert interacao.usuario is not None
    
    def test_interacao_str_representation(self):
        """Testa representação string da interação"""
        interacao = InteracaoClienteFactory(
            tipo_interacao='email',
            descricao='Contato por email'
        )
        expected = f"email - {interacao.cliente.nome_razao_social}"
        assert str(interacao) == expected
    
    def test_tipos_interacao_validos(self):
        """Testa tipos de interação válidos"""
        tipos_validos = ['email', 'telefone', 'reuniao', 'whatsapp']
        
        for tipo in tipos_validos:
            interacao = InteracaoClienteFactory(tipo_interacao=tipo)
            assert interacao.tipo_interacao == tipo


class TestClienteViews(TestCase):
    """Testes para views de clientes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.user = UserFactory()
        self.cliente = ClienteFactory()
    
    def test_lista_clientes_requer_login(self):
        """Testa que listagem requer autenticação"""
        url = reverse('clientes:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect para login
    
    def test_lista_clientes_autenticado(self):
        """Testa listagem com usuário autenticado"""
        self.client.force_login(self.user)
        url = reverse('clientes:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_detalhe_cliente(self):
        """Testa visualização de detalhes do cliente"""
        self.client.force_login(self.user)
        url = reverse('clientes:detalhe', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nome_razao_social)
    
    def test_criar_cliente_get(self):
        """Testa exibição do formulário de criação"""
        self.client.force_login(self.user)
        url = reverse('clientes:criar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_criar_cliente_post_valido(self):
        """Testa criação de cliente com dados válidos"""
        self.client.force_login(self.user)
        url = reverse('clientes:criar')
        
        data = {
            'nome_razao_social': 'Novo Cliente',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'novo@cliente.com',
            'telefone': '11999999999',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'cep': '01234567'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso
        
        # Verifica se cliente foi criado
        self.assertTrue(
            Cliente.objects.filter(nome_razao_social='Novo Cliente').exists()
        )
    
    def test_editar_cliente(self):
        """Testa edição de cliente"""
        self.client.force_login(self.user)
        url = reverse('clientes:editar', kwargs={'pk': self.cliente.pk})
        
        data = {
            'nome_razao_social': 'Cliente Editado',
            'tipo_pessoa': self.cliente.tipo_pessoa,
            'cpf_cnpj': self.cliente.cpf_cnpj,
            'email': self.cliente.email,
            'telefone': self.cliente.telefone,
            'endereco': self.cliente.endereco,
            'cidade': self.cliente.cidade,
            'uf': self.cliente.uf,
            'cep': self.cliente.cep
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verifica se foi editado
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nome_razao_social, 'Cliente Editado')
    
    def test_busca_clientes(self):
        """Testa busca de clientes"""
        self.client.force_login(self.user)
        
        # Criar cliente com nome específico
        ClienteFactory(nome_razao_social='Cliente Específico')
        
        url = reverse('clientes:lista')
        response = self.client.get(url, {'q': 'Específico'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Específico')
    
    def test_filtro_por_tipo_pessoa(self):
        """Testa filtro por tipo de pessoa"""
        self.client.force_login(self.user)
        
        # Criar clientes de tipos diferentes
        ClienteFactory(tipo_pessoa='PF')
        ClienteFactory(tipo_pessoa='PJ')
        
        url = reverse('clientes:lista')
        response = self.client.get(url, {'tipo_pessoa': 'PF'})
        
        self.assertEqual(response.status_code, 200)


class TestClienteForms(TestCase):
    """Testes para formulários de clientes"""
    
    def test_cliente_form_valido(self):
        """Testa formulário com dados válidos"""
        form_data = {
            'nome_razao_social': 'Cliente Teste',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'teste@cliente.com',
            'telefone': '11999999999',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'cep': '01234567'
        }
        
        form = ClienteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_cliente_form_email_invalido(self):
        """Testa formulário com email inválido"""
        form_data = {
            'nome_razao_social': 'Cliente Teste',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'email_invalido',
            'telefone': '11999999999'
        }
        
        form = ClienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_cliente_form_campos_obrigatorios(self):
        """Testa campos obrigatórios do formulário"""
        form = ClienteForm(data={})
        self.assertFalse(form.is_valid())
        
        campos_obrigatorios = ['nome_razao_social', 'tipo_pessoa', 'cpf_cnpj']
        for campo in campos_obrigatorios:
            self.assertIn(campo, form.errors)


class TestClienteAPI(APITestCase):
    """Testes para API de clientes"""
    
    def setUp(self):
        """Configuração inicial dos testes de API"""
        self.user = UserFactory()
        self.cliente = ClienteFactory()
    
    def test_lista_clientes_api_sem_auth(self):
        """Testa API sem autenticação"""
        url = reverse('api:clientes-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_lista_clientes_api_com_auth(self):
        """Testa API com autenticação"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:clientes-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_criar_cliente_api(self):
        """Testa criação via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:clientes-list')
        
        data = {
            'nome_razao_social': 'Cliente API',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '98765432101',
            'email': 'api@cliente.com',
            'telefone': '11888888888'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verifica se foi criado
        self.assertTrue(
            Cliente.objects.filter(nome_razao_social='Cliente API').exists()
        )
    
    def test_detalhe_cliente_api(self):
        """Testa detalhes via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:clientes-detail', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.cliente.pk)
    
    def test_atualizar_cliente_api(self):
        """Testa atualização via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:clientes-detail', kwargs={'pk': self.cliente.pk})
        
        data = {
            'nome_razao_social': 'Cliente Atualizado API',
            'tipo_pessoa': self.cliente.tipo_pessoa,
            'cpf_cnpj': self.cliente.cpf_cnpj,
            'email': self.cliente.email
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica se foi atualizado
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nome_razao_social, 'Cliente Atualizado API')


@pytest.mark.integration
class TestClienteIntegration:
    """Testes de integração para clientes"""
    
    @pytest.mark.django_db
    def test_fluxo_completo_cliente(self, authenticated_client, sample_data):
        """Testa fluxo completo: criar, listar, editar, visualizar"""
        client = authenticated_client
        
        # 1. Criar cliente
        create_url = reverse('clientes:criar')
        response = client.post(create_url, sample_data['cliente_data'])
        assert response.status_code == 302
        
        # 2. Verificar na listagem
        list_url = reverse('clientes:lista')
        response = client.get(list_url)
        assert response.status_code == 200
        assert sample_data['cliente_data']['nome_razao_social'] in response.content.decode()
        
        # 3. Buscar cliente criado
        cliente = Cliente.objects.get(
            nome_razao_social=sample_data['cliente_data']['nome_razao_social']
        )
        
        # 4. Visualizar detalhes
        detail_url = reverse('clientes:detalhe', kwargs={'pk': cliente.pk})
        response = client.get(detail_url)
        assert response.status_code == 200
        
        # 5. Editar cliente
        edit_url = reverse('clientes:editar', kwargs={'pk': cliente.pk})
        updated_data = sample_data['cliente_data'].copy()
        updated_data['nome_razao_social'] = 'Cliente Editado'
        
        response = client.post(edit_url, updated_data)
        assert response.status_code == 302
        
        # 6. Verificar edição
        cliente.refresh_from_db()
        assert cliente.nome_razao_social == 'Cliente Editado'
    
    @pytest.mark.django_db
    def test_cliente_com_interacoes(self, authenticated_client):
        """Testa cliente com interações"""
        client = authenticated_client
        cliente = ClienteFactory()
        
        # Criar interações
        InteracaoClienteFactory.create_batch(3, cliente=cliente)
        
        # Verificar na página de detalhes
        url = reverse('clientes:detalhe', kwargs={'pk': cliente.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'interacoes' in response.context
        assert response.context['cliente'].interacoes.count() == 3


@pytest.mark.slow
class TestClientePerformance:
    """Testes de performance para clientes"""
    
    @pytest.mark.django_db
    def test_listagem_com_muitos_clientes(self, authenticated_client):
        """Testa performance da listagem com muitos clientes"""
        import time
        
        # Criar muitos clientes
        ClienteFactory.create_batch(100)
        
        url = reverse('clientes:lista')
        
        start_time = time.time()
        response = authenticated_client.get(url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Deve ser rápido (< 2s)
    
    @pytest.mark.django_db
    def test_queries_otimizadas(self, authenticated_client):
        """Testa se as queries estão otimizadas"""
        from django.test.utils import override_settings
        from django.db import connection
        
        ClienteFactory.create_batch(10)
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            url = reverse('clientes:lista')
            response = authenticated_client.get(url)
            
            assert response.status_code == 200
            # Deve usar poucas queries (select_related/prefetch_related)
            assert len(connection.queries) < 10