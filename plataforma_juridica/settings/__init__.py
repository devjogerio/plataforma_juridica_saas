# Configurações do Django para Plataforma Jurídica SaaS

import os
import environ

# Inicializa o environ
env = environ.Env()

# Lê o arquivo .env se existir
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Determina qual configuração carregar baseado na variável ENVIRONMENT
environment = env('ENVIRONMENT', default='development')

if environment == 'production':
    from .production import *
elif environment == 'test':
    from .test import *
else:
    from .development import *