"""
Configurações de desenvolvimento para plataforma_juridica project.

Este arquivo herda as configurações base e adiciona configurações específicas
para o ambiente de desenvolvimento.
"""

from .base import *
import os

# DEBUG e ALLOWED_HOSTS são configurados no base.py através do arquivo .env

# Database - Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug toolbar e ferramentas de desenvolvimento
if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
        'silk',
    ]
    
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'silk.middleware.SilkyMiddleware',
        # 'querycount.middleware.QueryCountMiddleware',  # Temporariamente removido
    ]
    
    # Debug Toolbar Configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_TEMPLATE_CONTEXT': True,
        'IS_RUNNING_TESTS': False,
    }
    
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    
    # Silk Configuration
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_PYTHON_PROFILER_RESULT_PATH = '/tmp/'
    
    # Query Count Configuration
    QUERYCOUNT = {
        'THRESHOLDS': {
            'MEDIUM': 50,
            'HIGH': 200,
            'MIN_TIME_TO_LOG': 0,
            'MIN_QUERY_COUNT_TO_LOG': 5
        },
        'IGNORE_REQUEST_PATTERNS': [
            r'^/admin/',
            r'^/static/',
            r'^/media/',
        ],
        'IGNORE_SQL_PATTERNS': [],
        'DISPLAY_DUPLICATES': None,
        'RESPONSE_HEADER': 'X-DjangoQueryCount-Count'
    }

# Email backend para desenvolvimento
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache simples para desenvolvimento
if os.environ.get('USE_DUMMY_CACHE', 'False').lower() == 'true':
    # Usar cache em memória local para evitar dependência de Redis
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Logging mais verboso para desenvolvimento
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['plataforma_juridica']['level'] = 'DEBUG'