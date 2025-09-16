"""
Configurações e fixtures para pytest
"""
import pytest
import os
import django
from django.conf import settings

# Configurar Django ANTES de importar qualquer coisa do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plataforma_juridica.settings.test')
django.setup()

# Agora podemos importar com segurança
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from rest_framework.test import APIClient

from tests.factories import (
    UserFactory, AdminUserFactory, ClienteFactory, ProcessoFactory,
    ClienteCompletoFactory, ProcessoCompletoFactory
)

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configuração inicial do banco de dados para testes
    """
    with django_db_blocker.unblock():
        # Executar migrações se necessário
        call_command('migrate', '--run-syncdb')


@pytest.fixture
def user():
    """Fixture para usuário comum"""
    return UserFactory()


@pytest.fixture
def admin_user():
    """Fixture para usuário administrador"""
    return AdminUserFactory()


@pytest.fixture
def client():
    """Fixture para cliente Django de teste"""
    return Client()


@pytest.fixture
def authenticated_client(user):
    """Fixture para cliente autenticado"""
    from django.test import Client
    
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """Fixture para cliente admin autenticado"""
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def api_client():
    """Fixture para cliente de API REST"""
    return APIClient()


@pytest.fixture
def authenticated_api_client(user):
    """Fixture para cliente de API autenticado"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_api_client(admin_user):
    """Fixture para cliente de API admin"""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


# Fixtures para modelos
@pytest.fixture
def cliente():
    """Fixture para cliente simples"""
    return ClienteFactory()


@pytest.fixture
def cliente_pf():
    """Fixture para cliente pessoa física"""
    return ClienteFactory(pessoa_fisica=True)


@pytest.fixture
def cliente_pj():
    """Fixture para cliente pessoa jurídica"""
    return ClienteFactory(pessoa_juridica=True)


@pytest.fixture
def cliente_completo():
    """Fixture para cliente com relacionamentos"""
    return ClienteCompletoFactory()


@pytest.fixture
def processo():
    """Fixture para processo simples"""
    return ProcessoFactory()


@pytest.fixture
def processo_ativo():
    """Fixture para processo ativo"""
    return ProcessoFactory(ativo=True)


@pytest.fixture
def processo_encerrado():
    """Fixture para processo encerrado"""
    return ProcessoFactory(encerrado=True)


@pytest.fixture
def processo_completo():
    """Fixture para processo com relacionamentos"""
    return ProcessoCompletoFactory()


# Fixtures para listas de objetos
@pytest.fixture
def clientes_list():
    """Fixture para lista de clientes"""
    return ClienteFactory.create_batch(5)


@pytest.fixture
def processos_list():
    """Fixture para lista de processos"""
    return ProcessoFactory.create_batch(5)


# Fixtures para cenários específicos
@pytest.fixture
def cliente_com_processos(cliente):
    """Fixture para cliente com múltiplos processos"""
    ProcessoFactory.create_batch(3, cliente=cliente)
    return cliente


@pytest.fixture
def usuario_com_processos(user):
    """Fixture para usuário responsável por processos"""
    ProcessoFactory.create_batch(3, usuario_responsavel=user)
    return user


# Fixtures para dados de teste
@pytest.fixture
def sample_data():
    """Fixture com dados de exemplo para testes"""
    return {
        'cliente_data': {
            'nome_razao_social': 'Cliente Teste',
            'tipo_pessoa': 'PF',
            'cpf_cnpj': '12345678901',
            'email': 'cliente@teste.com',
            'telefone': '11999999999'
        },
        'processo_data': {
            'numero_processo': '1234567-89.2024.8.26.0001',
            'tipo_processo': 'Cível',
            'area_direito': 'Civil',
            'status': 'ativo',
            'valor_causa': '10000.00'
        }
    }


# Fixtures para configuração de cache
@pytest.fixture
def disable_cache(settings):
    """Desabilita cache durante os testes"""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


@pytest.fixture
def enable_cache(settings):
    """Habilita cache Redis para testes específicos"""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/15',  # DB 15 para testes
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }


# Fixtures para transações
@pytest.fixture
def transactional_db(db):
    """
    Fixture para testes que precisam de transações reais
    """
    return db


# Fixtures para arquivos de teste
@pytest.fixture
def sample_file():
    """Fixture para arquivo de teste"""
    import tempfile
    import os
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Conteúdo de teste')
        temp_file = f.name
    
    yield temp_file
    
    # Limpar arquivo após o teste
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_pdf():
    """Fixture para arquivo PDF de teste"""
    import tempfile
    import os
    from reportlab.pdfgen import canvas
    
    # Criar PDF temporário
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_file = f.name
    
    # Gerar PDF simples
    c = canvas.Canvas(temp_file)
    c.drawString(100, 750, "Documento de teste")
    c.save()
    
    yield temp_file
    
    # Limpar arquivo após o teste
    if os.path.exists(temp_file):
        os.unlink(temp_file)


# Configurações do pytest
def pytest_configure(config):
    """Configuração global do pytest"""
    import django
    from django.conf import settings
    
    # Configurar Django para testes
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            TESTING=True,
            USE_TZ=True,
            SECRET_KEY='test-secret-key',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            }
        )
    
    django.setup()


# Marcadores personalizados
def pytest_configure(config):
    """Registra marcadores personalizados"""
    config.addinivalue_line(
        "markers", "slow: marca testes como lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "api: marca testes de API"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )