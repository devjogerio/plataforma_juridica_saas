"""
Configurações específicas para ambiente de testes
"""

from .base import *
import tempfile
import copy

# Desabilitar DEBUG em testes para melhor performance
DEBUG = False

# Hosts permitidos para testes
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Remover apps de debug que podem interferir nos testes
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in [
    'debug_toolbar',
    'silk',
]]

# Remover middleware de debug
MIDDLEWARE = [mw for mw in MIDDLEWARE if mw not in [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'silk.middleware.SilkyMiddleware',
    'querycount.middleware.QueryCountMiddleware',
]]

# Database em memória para testes mais rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Cache dummy para testes (não persiste dados)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Sessões em banco de dados para testes (mais estável que cache)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Email backend para testes (não envia emails reais)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Desabilitar migrações para testes mais rápidos
class DisableMigrations:
    """
    Classe para desabilitar migrações durante os testes,
    acelerando significativamente a execução.
    """
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hashers mais rápidos para testes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Desabilitar logging durante testes para reduzir ruído
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
        'plataforma_juridica': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# Configurações de segurança desabilitadas para testes
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery em modo síncrono para testes
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Desabilitar throttling da API durante testes
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Configurações específicas para factories
FACTORY_BOY_SETTINGS = {
    'FAKER_LOCALE': 'pt_BR',
}

# Media root temporário para testes
MEDIA_ROOT = tempfile.mkdtemp()

# Configurações de templates otimizadas para testes
# Fazer uma cópia profunda para evitar modificar o original
TEMPLATES = copy.deepcopy(TEMPLATES)
TEMPLATES[0]['OPTIONS']['debug'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
TEMPLATES[0]['APP_DIRS'] = False

# Flag para desativar renderização de templates em algumas views durante testes
TEST_DISABLE_TEMPLATE_RENDER = True
