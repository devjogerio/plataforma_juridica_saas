"""
Testes de integração para fluxos completos do sistema
"""
import pytest
from datetime import date, timedelta
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status

from clientes.models import Cliente, InteracaoCliente
from processos.models import Processo, Andamento, Prazo
from documentos.models import Documento
from tests.factories import (
    UserFactory, ClienteFactory, ProcessoFactory,
    ClienteCompletoFactory, ProcessoCompletoFactory,
    InteracaoClienteFactory, AndamentoFactory,
    PrazoFactory, DocumentoFactory
)

User = get_user_model()


@pytest.mark.integration
class TestFluxoCompletoAdvogado:
    """Testa fluxo completo de um advogado usando o sistema"""
    
    @pytest.mark.django_db
    def test_dia_trabalho_advogado(self, authenticated_client):
        """Simula um dia de trabalho completo de um advogado"""
        client = authenticated_client
        
        # 1. Login e acesso ao dashboard
        dashboard_url = reverse('core:dashboard')
        response = client.get(dashboard_url)
        assert response.status_code == 200
        
        # 2. Cadastrar novo cliente
        create_client_url = reverse('clientes:criar')
        client_data = {
            'nome_razao_social': 'João Silva',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'joao@email.com',
            'telefone': '11999999999',
            'endereco': 'Rua A, 123',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'cep': '01234567'
        }
        
        response = client.post(create_client_url, client_data)
        assert response.status_code == 302
        
        # Buscar cliente criado
        cliente = Cliente.objects.get(nome_razao_social='João Silva')
        
        # 3. Registrar interação com cliente
        interaction_url = reverse('clientes:criar_interacao', kwargs={'cliente_pk': cliente.pk})
        interaction_data = {
            'tipo_interacao': 'reuniao',
            'descricao': 'Reunião inicial para discussão do caso',
            'data_interacao': date.today().strftime('%Y-%m-%d'),
            'observacoes': 'Cliente interessado em ação trabalhista'
        }
        
        response = client.post(interaction_url, interaction_data)
        assert response.status_code == 302
        
        # 4. Criar processo para o cliente
        create_process_url = reverse('processos:criar')
        process_data = {
            'numero_processo': '1000001-11.2023.5.02.0001',
            'cliente': cliente.pk,
            'tipo_processo': 1,  # Assumindo que existe
            'tribunal': 1,       # Assumindo que existe
            'assunto': 'Ação trabalhista - horas extras',
            'valor_causa': '15000.00',
            'status': 'ativo',
            'data_distribuicao': date.today().strftime('%Y-%m-%d')
        }
        
        response = client.post(create_process_url, process_data)
        assert response.status_code == 302
        
        # Buscar processo criado
        processo = Processo.objects.get(numero_processo='1000001-11.2023.5.02.0001')
        
        # 5. Adicionar andamento inicial
        andamento_url = reverse('processos:criar_andamento', kwargs={'pk': processo.pk})
        andamento_data = {
            'tipo_andamento': 'peticao',
            'descricao': 'Petição inicial protocolada',
            'data_andamento': date.today().strftime('%Y-%m-%d'),
            'observacoes': 'Protocolo eletrônico realizado com sucesso'
        }
        
        response = client.post(andamento_url, andamento_data)
        assert response.status_code == 302
        
        # 6. Criar prazo para contestação
        prazo_url = reverse('processos:criar_prazo', kwargs={'pk': processo.pk})
        prazo_data = {
            'descricao': 'Prazo para contestação da ré',
            'data_vencimento': (date.today() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'tipo_prazo': 'contestacao',
            'observacoes': 'Acompanhar se a ré irá contestar'
        }
        
        response = client.post(prazo_url, prazo_data)
        assert response.status_code == 302
        
        # 7. Verificar dashboard atualizado
        response = client.get(dashboard_url)
        assert response.status_code == 200
        
        # Verificar se as informações aparecem no dashboard
        content = response.content.decode()
        assert 'João Silva' in content
        assert '1000001-11.2023.5.02.0001' in content
        
        # 8. Verificar relatórios
        reports_url = reverse('core:relatorios')
        response = client.get(reports_url)
        assert response.status_code == 200
        
        # Verificar se cliente e processo aparecem nos relatórios
        assert Cliente.objects.filter(nome_razao_social='João Silva').exists()
        assert Processo.objects.filter(numero_processo='1000001-11.2023.5.02.0001').exists()
        assert Andamento.objects.filter(processo=processo).exists()
        assert Prazo.objects.filter(processo=processo).exists()
    
    @pytest.mark.django_db
    def test_gestao_prazos_completa(self, authenticated_client):
        """Testa gestão completa de prazos"""
        client = authenticated_client
        
        # Criar processo com prazos
        processo = ProcessoFactory()
        
        # Prazo vencendo hoje
        prazo_hoje = PrazoFactory(
            processo=processo,
            data_vencimento=date.today(),
            cumprido=False,
            descricao='Prazo vencendo hoje'
        )
        
        # Prazo vencendo em 3 dias
        prazo_futuro = PrazoFactory(
            processo=processo,
            data_vencimento=date.today() + timedelta(days=3),
            cumprido=False,
            descricao='Prazo futuro'
        )
        
        # Prazo já vencido
        prazo_vencido = PrazoFactory(
            processo=processo,
            data_vencimento=date.today() - timedelta(days=2),
            cumprido=False,
            descricao='Prazo vencido'
        )
        
        # 1. Verificar página de prazos
        prazos_url = reverse('processos:prazos')
        response = client.get(prazos_url)
        assert response.status_code == 200
        
        # 2. Verificar prazos vencendo
        prazos_vencendo_url = reverse('processos:prazos_vencendo')
        response = client.get(prazos_vencendo_url)
        assert response.status_code == 200
        
        content = response.content.decode()
        assert 'Prazo vencendo hoje' in content
        assert 'Prazo futuro' in content
        
        # 3. Marcar prazo como cumprido
        cumprir_url = reverse('processos:cumprir_prazo', kwargs={'pk': prazo_hoje.pk})
        response = client.post(cumprir_url)
        assert response.status_code == 302
        
        # Verificar se foi marcado como cumprido
        prazo_hoje.refresh_from_db()
        assert prazo_hoje.cumprido is True
        
        # 4. Verificar dashboard com alertas de prazos
        dashboard_url = reverse('core:dashboard')
        response = client.get(dashboard_url)
        assert response.status_code == 200
        
        # Deve mostrar prazos vencidos e vencendo
        content = response.content.decode()
        assert 'Prazo vencido' in content or 'prazos vencidos' in content.lower()


@pytest.mark.integration
class TestFluxoClienteProcesso:
    """Testa integração entre clientes e processos"""
    
    @pytest.mark.django_db
    def test_cliente_multiplos_processos(self, authenticated_client):
        """Testa cliente com múltiplos processos"""
        client = authenticated_client
        
        # Criar cliente
        cliente = ClienteFactory(nome_razao_social='Empresa ABC Ltda')
        
        # Criar múltiplos processos para o cliente
        processo1 = ProcessoFactory(
            cliente=cliente,
            numero_processo='1000001-11.2023.8.26.0001',
            assunto='Ação de cobrança'
        )
        
        processo2 = ProcessoFactory(
            cliente=cliente,
            numero_processo='2000002-22.2023.8.26.0001',
            assunto='Ação trabalhista'
        )
        
        processo3 = ProcessoFactory(
            cliente=cliente,
            numero_processo='3000003-33.2023.8.26.0001',
            assunto='Ação cível'
        )
        
        # Adicionar andamentos em cada processo
        AndamentoFactory(processo=processo1, descricao='Petição inicial - cobrança')
        AndamentoFactory(processo=processo2, descricao='Petição inicial - trabalhista')
        AndamentoFactory(processo=processo3, descricao='Petição inicial - cível')
        
        # Adicionar prazos
        PrazoFactory(processo=processo1, descricao='Contestação - cobrança')
        PrazoFactory(processo=processo2, descricao='Contestação - trabalhista')
        
        # Verificar página do cliente
        cliente_url = reverse('clientes:detalhe', kwargs={'pk': cliente.pk})
        response = client.get(cliente_url)
        assert response.status_code == 200
        
        content = response.content.decode()
        
        # Verificar se todos os processos aparecem
        assert '1000001-11.2023.8.26.0001' in content
        assert '2000002-22.2023.8.26.0001' in content
        assert '3000003-33.2023.8.26.0001' in content
        
        # Verificar se os assuntos aparecem
        assert 'Ação de cobrança' in content
        assert 'Ação trabalhista' in content
        assert 'Ação cível' in content
        
        # Verificar contadores
        assert cliente.processos.count() == 3
        
        # Verificar página de processos filtrada por cliente
        processos_url = reverse('processos:lista')
        response = client.get(processos_url, {'cliente': cliente.pk})
        assert response.status_code == 200
        
        # Deve mostrar apenas os processos deste cliente
        content = response.content.decode()
        assert content.count('Empresa ABC Ltda') >= 3
    
    @pytest.mark.django_db
    def test_historico_interacoes_cliente(self, authenticated_client):
        """Testa histórico completo de interações com cliente"""
        client = authenticated_client
        
        cliente = ClienteFactory()
        
        # Criar várias interações ao longo do tempo
        interacoes_data = [
            {
                'tipo_interacao': 'email',
                'descricao': 'Primeiro contato por email',
                'data_interacao': date.today() - timedelta(days=30)
            },
            {
                'tipo_interacao': 'telefone',
                'descricao': 'Ligação para esclarecimentos',
                'data_interacao': date.today() - timedelta(days=25)
            },
            {
                'tipo_interacao': 'reuniao',
                'descricao': 'Reunião presencial',
                'data_interacao': date.today() - timedelta(days=20)
            },
            {
                'tipo_interacao': 'whatsapp',
                'descricao': 'Mensagem via WhatsApp',
                'data_interacao': date.today() - timedelta(days=10)
            },
            {
                'tipo_interacao': 'email',
                'descricao': 'Envio de documentos',
                'data_interacao': date.today() - timedelta(days=5)
            }
        ]
        
        for interacao_data in interacoes_data:
            InteracaoClienteFactory(
                cliente=cliente,
                **interacao_data
            )
        
        # Verificar página do cliente
        cliente_url = reverse('clientes:detalhe', kwargs={'pk': cliente.pk})
        response = client.get(cliente_url)
        assert response.status_code == 200
        
        content = response.content.decode()
        
        # Verificar se todas as interações aparecem
        assert 'Primeiro contato por email' in content
        assert 'Ligação para esclarecimentos' in content
        assert 'Reunião presencial' in content
        assert 'Mensagem via WhatsApp' in content
        assert 'Envio de documentos' in content
        
        # Verificar ordenação cronológica (mais recente primeiro)
        interacoes = cliente.interacoes.all().order_by('-data_interacao')
        assert interacoes.count() == 5
        assert interacoes.first().descricao == 'Envio de documentos'
        assert interacoes.last().descricao == 'Primeiro contato por email'


@pytest.mark.integration
class TestFluxoDocumentos:
    """Testa fluxo completo de documentos"""
    
    @pytest.mark.django_db
    def test_gestao_documentos_processo(self, authenticated_client):
        """Testa gestão completa de documentos de um processo"""
        client = authenticated_client
        
        processo = ProcessoFactory()
        
        # Criar diferentes tipos de documentos
        documentos_data = [
            {
                'nome': 'Petição Inicial',
                'tipo_documento': 'peticao',
                'descricao': 'Petição inicial do processo'
            },
            {
                'nome': 'Procuração',
                'tipo_documento': 'procuracao',
                'descricao': 'Procuração do cliente'
            },
            {
                'nome': 'Contrato de Trabalho',
                'tipo_documento': 'contrato',
                'descricao': 'Contrato de trabalho do autor'
            },
            {
                'nome': 'Certidão de Tempo de Serviço',
                'tipo_documento': 'certidao',
                'descricao': 'Certidão emitida pela empresa'
            }
        ]
        
        for doc_data in documentos_data:
            DocumentoFactory(
                processo=processo,
                **doc_data
            )
        
        # Verificar página do processo
        processo_url = reverse('processos:detalhe', kwargs={'pk': processo.pk})
        response = client.get(processo_url)
        assert response.status_code == 200
        
        content = response.content.decode()
        
        # Verificar se todos os documentos aparecem
        assert 'Petição Inicial' in content
        assert 'Procuração' in content
        assert 'Contrato de Trabalho' in content
        assert 'Certidão de Tempo de Serviço' in content
        
        # Verificar contadores
        assert processo.documentos.count() == 4
        
        # Verificar página específica de documentos
        documentos_url = reverse('documentos:processo', kwargs={'processo_id': processo.pk})
        response = client.get(documentos_url)
        assert response.status_code == 200
        
        # Verificar filtros por tipo
        response = client.get(documentos_url, {'tipo': 'peticao'})
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Petição Inicial' in content


class TestIntegracaoAPI(APITestCase):
    """Testes de integração da API"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_fluxo_completo_api(self):
        """Testa fluxo completo via API"""
        
        # 1. Criar cliente via API
        clientes_url = reverse('api:clientes-list')
        cliente_data = {
            'nome_razao_social': 'Cliente API',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '11111111111',
            'email': 'cliente@api.com',
            'telefone': '11888888888'
        }
        
        response = self.client.post(clientes_url, cliente_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cliente_id = response.data['id']
        
        # 2. Criar processo via API
        processos_url = reverse('api:processos-list')
        processo_data = {
            'numero_processo': '9999999-99.2023.8.26.0001',
            'cliente': cliente_id,
            'assunto': 'Processo via API',
            'status': 'ativo'
        }
        
        response = self.client.post(processos_url, processo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        processo_id = response.data['id']
        
        # 3. Criar andamento via API
        andamentos_url = reverse('api:andamentos-list')
        andamento_data = {
            'processo': processo_id,
            'tipo_andamento': 'peticao',
            'descricao': 'Andamento via API',
            'data_andamento': date.today().isoformat()
        }
        
        response = self.client.post(andamentos_url, andamento_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 4. Criar prazo via API
        prazos_url = reverse('api:prazos-list')
        prazo_data = {
            'processo': processo_id,
            'descricao': 'Prazo via API',
            'data_vencimento': (date.today() + timedelta(days=10)).isoformat(),
            'tipo_prazo': 'contestacao'
        }
        
        response = self.client.post(prazos_url, prazo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Verificar dados criados
        # Cliente
        response = self.client.get(f'{clientes_url}{cliente_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome_razao_social'], 'Cliente API')
        
        # Processo
        response = self.client.get(f'{processos_url}{processo_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assunto'], 'Processo via API')
        
        # Verificar relacionamentos
        self.assertEqual(response.data['cliente'], cliente_id)
        
        # 6. Testar filtros e buscas
        # Buscar processos por cliente
        response = self.client.get(processos_url, {'cliente': cliente_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Buscar andamentos por processo
        response = self.client.get(andamentos_url, {'processo': processo_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Buscar prazos por processo
        response = self.client.get(prazos_url, {'processo': processo_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_validacoes_api(self):
        """Testa validações da API"""
        
        # Tentar criar cliente com dados inválidos
        clientes_url = reverse('api:clientes-list')
        cliente_data = {
            'nome_razao_social': '',  # Campo obrigatório vazio
            'tipo_pessoa': 'INVALID',  # Tipo inválido
            'email': 'email_invalido'  # Email inválido
        }
        
        response = self.client.post(clientes_url, cliente_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verificar se os erros estão presentes
        self.assertIn('nome_razao_social', response.data)
        self.assertIn('tipo_pessoa', response.data)
        self.assertIn('email', response.data)
        
        # Tentar criar processo com número duplicado
        cliente = ClienteFactory()
        ProcessoFactory(numero_processo='1111111-11.2023.8.26.0001')
        
        processos_url = reverse('api:processos-list')
        processo_data = {
            'numero_processo': '1111111-11.2023.8.26.0001',  # Número duplicado
            'cliente': cliente.pk,
            'assunto': 'Processo duplicado'
        }
        
        response = self.client.post(processos_url, processo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('numero_processo', response.data)


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Testes de performance e integração"""
    
    @pytest.mark.django_db
    def test_dashboard_com_muitos_dados(self, authenticated_client):
        """Testa performance do dashboard com muitos dados"""
        import time
        
        # Criar muitos dados
        clientes = ClienteFactory.create_batch(20)
        processos = []
        
        for cliente in clientes:
            # 2-3 processos por cliente
            cliente_processos = ProcessoFactory.create_batch(2, cliente=cliente)
            processos.extend(cliente_processos)
        
        # Adicionar andamentos e prazos
        for processo in processos[:10]:  # Apenas nos primeiros 10 para não ser muito lento
            AndamentoFactory.create_batch(3, processo=processo)
            PrazoFactory.create_batch(2, processo=processo)
        
        # Testar performance do dashboard
        dashboard_url = reverse('core:dashboard')
        
        start_time = time.time()
        response = authenticated_client.get(dashboard_url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Deve carregar em menos de 5 segundos
        
        # Verificar se os dados aparecem
        content = response.content.decode()
        assert 'clientes' in content.lower()
        assert 'processos' in content.lower()
    
    @pytest.mark.django_db
    def test_busca_global_performance(self, authenticated_client):
        """Testa performance da busca global"""
        import time
        
        # Criar dados para busca
        ClienteFactory.create_batch(30, nome_razao_social='Cliente Teste')
        ProcessoFactory.create_batch(20, assunto='Processo Teste')
        
        # Testar busca
        search_url = reverse('core:busca_global')
        
        start_time = time.time()
        response = authenticated_client.get(search_url, {'q': 'Teste'})
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Busca deve ser rápida
        
        # Verificar resultados
        content = response.content.decode()
        assert 'Cliente Teste' in content
        assert 'Processo Teste' in content


class TestTransacionalIntegration(TransactionTestCase):
    """Testes que requerem controle de transações"""
    
    def test_rollback_em_erro(self):
        """Testa rollback em caso de erro"""
        
        # Criar cliente
        cliente = ClienteFactory()
        
        try:
            with transaction.atomic():
                # Criar processo
                processo = ProcessoFactory(cliente=cliente)
                
                # Simular erro que deve causar rollback
                raise Exception("Erro simulado")
                
        except Exception:
            pass
        
        # Verificar se o processo não foi salvo devido ao rollback
        assert not Processo.objects.filter(cliente=cliente).exists()
        
        # Mas o cliente deve existir (foi criado fora da transação)
        assert Cliente.objects.filter(pk=cliente.pk).exists()
    
    def test_integridade_dados(self):
        """Testa integridade dos dados em operações complexas"""
        
        cliente = ClienteFactory()
        
        with transaction.atomic():
            # Criar processo
            processo = ProcessoFactory(cliente=cliente)
            
            # Criar andamentos
            andamentos = AndamentoFactory.create_batch(3, processo=processo)
            
            # Criar prazos
            prazos = PrazoFactory.create_batch(2, processo=processo)
            
            # Verificar integridade
            assert processo.andamentos.count() == 3
            assert processo.prazos.count() == 2
            
            # Verificar relacionamentos
            for andamento in andamentos:
                assert andamento.processo == processo
            
            for prazo in prazos:
                assert prazo.processo == processo


@pytest.mark.integration
class TestFluxoFinanceiroCompleto:
    """Testa fluxos financeiros completos"""
    
    @pytest.mark.django_db
    def test_ciclo_cobranca_completo(self, authenticated_client):
        """Testa ciclo completo de cobrança: criação -> vencimento -> pagamento"""
        from financeiro.models import Honorario, ParcelaHonorario
        from decimal import Decimal
        
        client = authenticated_client
        cliente = ClienteFactory()
        processo = ProcessoFactory(cliente=cliente)
        
        # 1. Criar honorário
        honorario = Honorario.objects.create(
            cliente=cliente,
            processo=processo,
            tipo_cobranca='fixo',
            valor_fixo=Decimal('2000.00'),
            valor_total=Decimal('2000.00'),
            data_vencimento=date.today() + timedelta(days=30),
            numero_parcelas=2,
            observacoes='Honorários advocatícios'
        )
        
        # 2. Gerar parcelas
        honorario.gerar_parcelas()
        
        # 3. Verificar se as parcelas foram criadas
        parcelas = ParcelaHonorario.objects.filter(honorario=honorario)
        assert parcelas.count() == 2
        
        # 4. Verificar valor das parcelas
        for parcela in parcelas:
            assert parcela.valor_parcela == Decimal('1000.00')
            assert parcela.status == 'pendente'
        
        # 5. Simular pagamento da primeira parcela
        primeira_parcela = parcelas.first()
        primeira_parcela.marcar_como_paga(
            valor_pago=Decimal('1000.00'),
            data_pagamento=date.today()
        )
        
        # 6. Verificar status após pagamento
        primeira_parcela.refresh_from_db()
        assert primeira_parcela.status == 'pago'
        assert primeira_parcela.valor_pago == Decimal('1000.00')
        
        # 7. Verificar status do honorário
        honorario.refresh_from_db()
        assert honorario.status_pagamento == 'parcial'
    
    @pytest.mark.django_db
    def test_relatorio_financeiro_integrado(self, authenticated_client):
        """Testa geração de relatório financeiro integrado"""
        from financeiro.models import Honorario
        from decimal import Decimal
        
        client = authenticated_client
        
        # Criar clientes e processos de teste
        clientes = ClienteFactory.create_batch(3)
        
        for cliente in clientes:
            processo = ProcessoFactory(cliente=cliente)
            Honorario.objects.create(
                cliente=cliente,
                processo=processo,
                tipo_cobranca='fixo',
                valor_fixo=Decimal('1000.00'),
                valor_total=Decimal('1000.00'),
                data_vencimento=date.today() + timedelta(days=30),
                observacoes=f'Honorários {cliente.nome_razao_social}'
            )
        
        # Verificar se os dados foram criados corretamente
        total_honorarios = Honorario.objects.count()
        assert total_honorarios == 3
        
        # Verificar valor total
        from django.db.models import Sum
        total_valor = Honorario.objects.aggregate(
            total=Sum('valor_total')
        )['total']
        assert total_valor == Decimal('3000.00')


@pytest.mark.integration
class TestFluxoNotificacoes:
    """Testa sistema de notificações integrado"""
    
    @pytest.mark.django_db
    def test_notificacao_prazo_vencimento(self, authenticated_client):
        """Testa notificação automática de prazo vencendo"""
        from notificacoes.models import Notificacao
        from unittest.mock import patch
        
        client = authenticated_client
        user = client.user if hasattr(client, 'user') else UserFactory()
        
        # Criar prazo vencendo
        processo = ProcessoFactory()
        prazo = PrazoFactory(
            processo=processo,
            data_vencimento=date.today() + timedelta(days=2),
            responsavel=user
        )
        
        # Simular task de verificação de prazos
        with patch('notificacoes.tasks.enviar_email_notificacao.delay') as mock_email:
            from notificacoes.services import verificar_prazos_vencimento
            verificar_prazos_vencimento()
            
            # Verificar se notificação foi criada
            notificacao = Notificacao.objects.filter(
                usuario=user,
                tipo='prazo_vencimento'
            ).first()
            
            assert notificacao is not None
            assert str(prazo.id) in notificacao.conteudo
            mock_email.assert_called_once()
    
    @pytest.mark.django_db
    def test_alerta_processo_sem_andamento(self, authenticated_client):
        """Testa alerta para processo sem andamento há muito tempo"""
        from alertas.models import Alerta
        
        # Criar processo antigo sem andamentos recentes
        processo = ProcessoFactory(
            data_distribuicao=date.today() - timedelta(days=90)
        )
        
        # Último andamento há 60 dias
        AndamentoFactory(
            processo=processo,
            data_andamento=date.today() - timedelta(days=60)
        )
        
        # Executar verificação de alertas
        from alertas.services import verificar_processos_sem_andamento
        verificar_processos_sem_andamento()
        
        # Verificar se alerta foi criado
        alerta = Alerta.objects.filter(
            tipo='processo_sem_andamento',
            objeto_id=processo.id
        ).first()
        
        assert alerta is not None
        assert alerta.nivel == 'warning'


@pytest.mark.integration
class TestFluxoRelatoriosAvancados:
    """Testa geração de relatórios avançados e dashboards"""
    
    @pytest.mark.django_db
    def test_dashboard_metricas_tempo_real(self, authenticated_client):
        """Testa dashboard com métricas em tempo real"""
        client = authenticated_client
        
        # Criar dados variados
        clientes = ClienteFactory.create_batch(10)
        processos_ativos = [ProcessoFactory(cliente=cliente) for cliente in clientes[:7]]
        processos_arquivados = [ProcessoFactory(cliente=cliente, ativo=False) for cliente in clientes[7:]]
        
        # Adicionar andamentos recentes
        for processo in processos_ativos[:3]:
            AndamentoFactory(
                processo=processo,
                data_andamento=date.today()
            )
        
        # Acessar dashboard
        dashboard_url = reverse('core:dashboard')
        response = client.get(dashboard_url)
        assert response.status_code == 200
        
        context = response.context
        assert context['total_clientes'] == 10
        assert context['processos_ativos'] == 7
        assert context['processos_arquivados'] == 3
        assert context['andamentos_hoje'] == 3
    
    @pytest.mark.django_db
    def test_relatorio_produtividade_advogado(self, authenticated_client):
        """Testa relatório de produtividade por advogado"""
        client = authenticated_client
        user = UserFactory()
        
        # Criar processos atribuídos ao advogado
        processos = ProcessoFactory.create_batch(5, responsavel=user)
        
        # Adicionar andamentos
        for processo in processos:
            AndamentoFactory.create_batch(3, processo=processo, usuario=user)
        
        # Gerar relatório
        relatorio_url = reverse('relatorios:produtividade_advogado', args=[user.id])
        response = client.get(relatorio_url)
        assert response.status_code == 200
        
        context = response.context
        assert context['total_processos'] == 5
        assert context['total_andamentos'] == 15
        assert context['media_andamentos_processo'] == 3.0
    
    @pytest.mark.django_db
    def test_exportacao_relatorio_excel(self, authenticated_client):
        """Testa exportação de relatório em Excel"""
        client = authenticated_client
        
        # Criar dados para exportação
        ClienteFactory.create_batch(5)
        
        # Solicitar exportação
        export_url = reverse('relatorios:clientes_excel')
        response = client.get(export_url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'attachment' in response['Content-Disposition']


@pytest.mark.integration
@pytest.mark.slow
class TestFluxoPerformanceCritico:
    """Testa cenários críticos de performance"""
    
    @pytest.mark.django_db
    def test_listagem_processos_otimizada(self, authenticated_client):
        """Testa se listagem de processos está otimizada com select_related/prefetch_related"""
        from django.test.utils import override_settings
        from django.db import connection
        
        client = authenticated_client
        
        # Criar muitos dados relacionados
        clientes = ClienteFactory.create_batch(20)
        processos = []
        for cliente in clientes:
            processo = ProcessoFactory(cliente=cliente)
            processos.append(processo)
            AndamentoFactory.create_batch(3, processo=processo)
            PrazoFactory.create_batch(2, processo=processo)
        
        # Testar listagem com contagem de queries
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            list_url = reverse('processos:list')
            response = client.get(list_url)
            
            assert response.status_code == 200
            # Deve usar no máximo 5 queries independente da quantidade de dados
            assert len(connection.queries) <= 5
    
    @pytest.mark.django_db
    def test_busca_global_performance(self, authenticated_client):
        """Testa performance da busca global"""
        import time
        
        client = authenticated_client
        
        # Criar muitos dados para busca
        ClienteFactory.create_batch(100)
        ProcessoFactory.create_batch(100)
        
        # Testar busca
        start_time = time.time()
        
        search_url = reverse('core:busca_global')
        response = client.get(search_url, {'q': 'Silva'})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert response.status_code == 200
        assert execution_time < 2.0  # Deve executar em menos de 2 segundos
    
    @pytest.mark.django_db
    def test_cache_dashboard_funcionando(self, authenticated_client):
        """Testa se cache do dashboard está funcionando corretamente"""
        from django.core.cache import cache
        
        client = authenticated_client
        
        # Limpar cache
        cache.clear()
        
        # Primeira requisição - deve calcular
        dashboard_url = reverse('core:dashboard')
        response1 = client.get(dashboard_url)
        
        # Segunda requisição - deve vir do cache
        response2 = client.get(dashboard_url)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verificar se dados estão no cache
        cached_data = cache.get('dashboard_metrics')
        assert cached_data is not None


@pytest.mark.integration
class TestFluxoSeguranca:
    """Testa aspectos de segurança integrados"""
    
    @pytest.mark.django_db
    def test_controle_acesso_por_permissao(self, client):
        """Testa controle de acesso baseado em permissões"""
        from django.contrib.auth.models import Permission
        
        # Usuário sem permissões
        user_sem_permissao = UserFactory()
        client.force_login(user_sem_permissao)
        
        # Tentar acessar área restrita
        admin_url = reverse('admin:index')
        response = client.get(admin_url)
        assert response.status_code in [302, 403]  # Redirect ou forbidden
        
        # Usuário com permissões
        user_com_permissao = UserFactory(is_staff=True)
        client.force_login(user_com_permissao)
        
        response = client.get(admin_url)
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_auditoria_alteracoes(self, authenticated_client):
        """Testa se alterações estão sendo auditadas"""
        from core.models import LogAuditoria
        
        client = authenticated_client
        cliente = ClienteFactory()
        
        # Fazer alteração
        update_url = reverse('clientes:update', args=[cliente.id])
        response = client.post(update_url, {
            'nome_razao_social': 'Nome Alterado',
            'tipo_pessoa': cliente.tipo_pessoa,
            'cpf_cnpj': cliente.cpf_cnpj,
            'email': cliente.email,
            'telefone': cliente.telefone,
            'endereco': cliente.endereco,
            'cidade': cliente.cidade,
            'estado': cliente.estado,
            'cep': cliente.cep,
        })
        
        # Verificar se log de auditoria foi criado
        log = LogAuditoria.objects.filter(
            modelo='Cliente',
            objeto_id=cliente.id,
            acao='update'
        ).first()
        
        assert log is not None
        assert 'nome_razao_social' in log.campos_alterados
    
    @pytest.mark.django_db
    def test_validacao_csrf_protecao(self, client):
        """Testa se proteção CSRF está funcionando"""
        user = UserFactory()
        client.force_login(user)
        
        # Tentar POST sem token CSRF
        create_url = reverse('clientes:criar')
        response = client.post(create_url, {
            'nome_razao_social': 'Teste CSRF',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'teste@email.com',
        }, HTTP_X_CSRFTOKEN='')
        
        # Deve falhar por falta de token CSRF
        assert response.status_code == 403