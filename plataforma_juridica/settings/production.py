"""
Configurações de produção para plataforma_juridica project.

Este arquivo herda as configurações base e adiciona configurações específicas
para o ambiente de produção, focando em segurança e performance.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Configurações de segurança para produção
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Configurações adicionais de segurança
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TZ = True

# Cache de templates para melhor performance
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
TEMPLATES[0]['APP_DIRS'] = False

# Configurações de cache otimizadas para produção
CACHES['default']['TIMEOUT'] = 3600  # 1 hora
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS']['max_connections'] = 50

# Configurações de sessão para produção
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Configurações de email para produção
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configurações de logging para produção
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['handlers']['console']['level'] = 'ERROR'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['plataforma_juridica']['level'] = 'INFO'

# Adicionar handler para erros críticos
LOGGING['handlers']['mail_admins'] = {
    'level': 'ERROR',
    'class': 'django.utils.log.AdminEmailHandler',
    'include_html': True,
}
LOGGING['loggers']['django']['handlers'].append('mail_admins')

# Configurações de administradores para notificações de erro
ADMINS = env.list('ADMINS', default=[])
MANAGERS = ADMINS

# Configurações de compressão de arquivos estáticos
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Configurações de middleware para produção
MIDDLEWARE.insert(1, 'django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.append('django.middleware.cache.FetchFromCacheMiddleware')

# Configurações de cache de páginas
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutos
CACHE_MIDDLEWARE_KEY_PREFIX = 'plataforma_juridica_page'

# Configurações de throttling mais restritivas para produção
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '50/hour',
    'user': '500/hour'
}

# Configurações de Celery para produção
CELERY_TASK_ROUTES = {
    'plataforma_juridica.tasks.heavy_task': {'queue': 'heavy'},
    'plataforma_juridica.tasks.light_task': {'queue': 'light'},
}

# Configurações de monitoramento
if env('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env('ENVIRONMENT', default='production'),
    )