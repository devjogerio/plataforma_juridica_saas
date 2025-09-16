"""
Configurações do Django para plataforma_juridica project.

Este arquivo determina qual configuração usar baseado na variável de ambiente
DJANGO_SETTINGS_MODULE ou ENVIRONMENT.
"""

import os

# Determinar qual ambiente usar
environment = os.environ.get('ENVIRONMENT', 'development')

if environment == 'production':
    from .settings.production import *
elif environment == 'test':
    from .settings.test import *
else:
    from .settings.development import *