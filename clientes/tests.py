from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from unittest.mock import patch
from .models import Cliente, InteracaoCliente
from .forms import ClienteForm
import uuid

User = get_user_model()


class ClienteModelTest(TestCase):
    """Testes para o modelo Cliente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_criar_cliente_pessoa_fisica(self):
        """Testa criação de cliente pessoa física"""
        cliente = Cliente.objects.create(
            tipo_pessoa='PF',
            nome_razao_social='João Silva',
            cpf_cnpj='123.456.789-00',
            email='joao@example.com',
            telefone='(11) 99999-9999'
        )
        
        self.assertEqual(cliente.tipo_pessoa, 'PF')
        self.assertEqual(cliente.nome_razao_social, 'João Silva')
        self.assertEqual(cliente.cpf_cnpj, '123.456.789-00')
        self.assertTrue(cliente.ativo)
        self.assertIsInstance(cliente.id, uuid.UUID)
        
    def test_criar_cliente_pessoa_juridica(self):
        """Testa criação de cliente pessoa jurídica"""
        cliente = Cliente.objects.create(
            tipo_pessoa='PJ',
            nome_razao_social='Empresa LTDA',
            cpf_cnpj='12.345.678/0001-90',
            email='empresa@example.com'
        )
        
        self.assertEqual(cliente.tipo_pessoa, 'PJ')
        self.assertEqual(cliente.nome_razao_social, 'Empresa LTDA')
        self.assertEqual(cliente.cpf_cnpj, '12.345.678/0001-90')
        
    def test_str_representation(self):
        """Testa representação string do modelo"""
        cliente = Cliente.objects.create(
            tipo_pessoa='PF',
            nome_razao_social='Maria Santos',
            cpf_cnpj='987.654.321-00'
        )
        
        self.assertEqual(str(cliente), 'Maria Santos (Pessoa Física)')
        
    def test_documento_principal_property(self):
        """Testa propriedade documento_principal"""
        cliente = Cliente.objects.create(
            tipo_pessoa='PF',
            nome_razao_social='João Silva',
            cpf_cnpj='123.456.789-00'
        )
        
        self.assertEqual(cliente.documento_principal, '123.456.789-00')


class ClienteFormTest(TestCase):
    """Testes para o formulário ClienteForm"""
    
    def test_form_valido_pessoa_fisica(self):
        """Testa formulário válido para pessoa física"""
        form_data = {
            'tipo_pessoa': 'PF',
            'nome_razao_social': 'João Silva',
            'cpf_cnpj': '11144477735',  # CPF válido
            'email': 'joao@example.com',
            'telefone': '(11) 99999-9999',
            'ativo': True
        }
        
        form = ClienteForm(data=form_data)
        if not form.is_valid():
            print(f"Erros do formulário: {form.errors}")
        self.assertTrue(form.is_valid())
        
    def test_form_valido_pessoa_juridica(self):
        """Testa formulário válido para pessoa jurídica"""
        form_data = {
            'tipo_pessoa': 'PJ',
            'nome_razao_social': 'Empresa LTDA',
            'cpf_cnpj': '11222333000181',  # CNPJ válido
            'email': 'empresa@example.com',
            'ativo': True
        }
        
        form = ClienteForm(data=form_data)
        if not form.is_valid():
            print(f"Erros do formulário PJ: {form.errors}")
        self.assertTrue(form.is_valid())
        
    def test_form_invalido_sem_nome(self):
        """Testa formulário inválido sem nome"""
        form_data = {
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '123.456.789-00',
            'ativo': True
        }
        
        form = ClienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome_razao_social', form.errors)
        
    def test_form_invalido_sem_cpf_cnpj(self):
        """Testa formulário inválido sem CPF/CNPJ"""
        form_data = {
            'tipo_pessoa': 'PF',
            'nome_razao_social': 'João Silva',
            'ativo': True
        }
        
        form = ClienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf_cnpj', form.errors)


class ClienteViewTest(TestCase):
    """Testes para as views de Cliente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Criar cliente de teste
        self.cliente = Cliente.objects.create(
            tipo_pessoa='PF',
            nome_razao_social='João da Silva',
            cpf_cnpj='123.456.789-00',
            email='joao@example.com',
            telefone='(11) 99999-9999'
        )
        
    def test_criar_cliente_get(self):
        """Testa acesso à página de criação de cliente"""
        url = reverse('clientes:cadastrar')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
    def test_criar_cliente_post_valido(self):
        """Testa criação de cliente via POST com dados válidos"""
        url = reverse('clientes:cadastrar')
        data = {
            'tipo_pessoa': 'PF',
            'nome_razao_social': 'Maria Santos',
            'cpf_cnpj': '987.654.321-00',
            'email': 'maria@example.com',
            'telefone': '(11) 88888-8888',
            'ativo': True
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Verifica se o cliente foi criado
        self.assertTrue(Cliente.objects.filter(nome_razao_social='Maria Santos').exists())
        
        # Verifica mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sucesso' in str(message).lower() for message in messages))
        
    def test_criar_cliente_post_invalido(self):
        """Testa criação de cliente via POST com dados inválidos"""
        url = reverse('clientes:cadastrar')
        data = {
            'tipo_pessoa': 'PF',
            # nome_razao_social ausente
            'cpf_cnpj': '987.654.321-00',
            'ativo': True
        }
        
        response = self.client.post(url, data)
        
        # Verifica que permanece na mesma página
        self.assertEqual(response.status_code, 200)
        
        # Verifica que o cliente não foi criado
        self.assertFalse(Cliente.objects.filter(cpf_cnpj='987.654.321-00').exists())
        
    def test_detalhe_cliente(self):
        """Testa visualização de detalhes do cliente"""
        url = reverse('clientes:detalhe', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nome_razao_social)
        self.assertContains(response, self.cliente.cpf_cnpj)
        
    def test_lista_clientes(self):
        """Testa listagem de clientes"""
        url = reverse('clientes:lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nome_razao_social)
        
    def test_acesso_nao_autenticado(self):
        """Testa acesso sem autenticação"""
        self.client.logout()
        
        url = reverse('clientes:cadastrar')
        response = self.client.get(url)
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/') or '/login/' in response.url)
        
    def test_cliente_criado_corretamente(self):
        """Testa se o cliente é criado corretamente"""
        url = reverse('clientes:cadastrar')
        data = {
            'tipo_pessoa': 'PF',
            'nome_razao_social': 'Pedro Oliveira',
            'cpf_cnpj': '11144477735',  # CPF válido
            'ativo': True
        }
        
        response = self.client.post(url, data)
        
        # Verificar se houve redirecionamento (sucesso)
        if response.status_code != 302:
            print(f"Status code: {response.status_code}")
            print(f"Response content: {response.content}")
        
        cliente_criado = Cliente.objects.get(nome_razao_social='Pedro Oliveira')
        self.assertEqual(cliente_criado.nome_razao_social, 'Pedro Oliveira')
        self.assertEqual(cliente_criado.cpf_cnpj, '11144477735')
        self.assertTrue(cliente_criado.ativo)


class InteracaoClienteTest(TestCase):
    """Testes para o modelo InteracaoCliente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.cliente = Cliente.objects.create(
            tipo_pessoa='PF',
            nome_razao_social='João da Silva',
            cpf_cnpj='123.456.789-00',
            email='joao@example.com',
            telefone='(11) 99999-9999'
        )
        
    def test_criar_interacao(self):
        """Testa criação de interação com cliente"""
        from datetime import datetime
        
        interacao = InteracaoCliente.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            tipo_interacao='ligacao',
            data_interacao=datetime.now(),
            assunto='Consulta sobre processo',
            descricao='Cliente ligou para saber sobre andamento do processo'
        )
        
        self.assertEqual(interacao.cliente, self.cliente)
        self.assertEqual(interacao.usuario, self.user)
        self.assertEqual(interacao.tipo_interacao, 'ligacao')
        self.assertEqual(interacao.assunto, 'Consulta sobre processo')
        
    def test_str_representation_interacao(self):
        """Testa representação string da interação"""
        from datetime import datetime
        
        data_teste = datetime(2025, 9, 15, 10, 30)
        
        interacao = InteracaoCliente.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            tipo_interacao='email',
            data_interacao=data_teste,
            assunto='Envio de documentos',
            descricao='Enviados documentos por email'
        )
        
        expected_str = f"{self.cliente.nome_razao_social} - Envio de documentos (15/09/2025)"
        self.assertEqual(str(interacao), expected_str)
