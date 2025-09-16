# FASE 1 - OTIMIZAÇÃO DE PERFORMANCE

## 📊 Status da Implementação
- **Início**: Implementação iniciada
- **Duração Prevista**: 3 semanas
- **Responsável**: Desenvolvedor Backend Senior
- **Status Atual**: 🔄 Em andamento

## 🎯 Objetivos Específicos

### Métricas de Sucesso
| Métrica | Baseline | Meta | Status |
|---------|----------|------|--------|
| Tempo de resposta médio | ~800ms | ~480ms | 🔄 Medindo |
| Queries por request | 15-20 | 3-5 | 🔄 Analisando |
| Cache hit ratio | 0% | 80% | ⏳ Pendente |
| Throughput API | 50 req/s | 100 req/s | ⏳ Pendente |

## 📋 Implementação Detalhada

### Semana 1: Análise e Otimização de Queries

#### ✅ Configuração de Ferramentas de Análise

##### Django Debug Toolbar
```python
# settings.py - Configuração para análise de performance
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_TEMPLATE_CONTEXT': True,
    }
    
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

##### Django Silk para Profiling
```python
# settings.py - Configuração do Silk
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = '/tmp/'
```

#### 🔍 Análise de Queries N+1 Identificadas

##### 1. Views de Clientes
**Problema**: `clientes/views.py` - ClienteListView
```python
# ANTES - Gerando N+1 queries
class ClienteListView(ListView):
    model = Cliente
    template_name = 'clientes/lista.html'
    
    def get_queryset(self):
        return Cliente.objects.all()  # N+1 ao acessar processos relacionados
```

**Solução Implementada**:
```python
# DEPOIS - Otimizado com select_related e prefetch_related
class ClienteListView(ListView):
    model = Cliente
    template_name = 'clientes/lista.html'
    
    def get_queryset(self):
        return Cliente.objects.select_related(
            'usuario_responsavel',
            'empresa'
        ).prefetch_related(
            'processos__tipo_processo',
            'interacoes__usuario',
            'documentos'
        ).order_by('-data_cadastro')
```

##### 2. Views de Processos
**Problema**: `processos/views.py` - ProcessoDetailView
```python
# ANTES - Múltiplas queries desnecessárias
class ProcessoDetailView(DetailView):
    model = Processo
    template_name = 'processos/detalhe.html'
```

**Solução Implementada**:
```python
# DEPOIS - Otimizado para carregar relacionamentos
class ProcessoDetailView(DetailView):
    model = Processo
    template_name = 'processos/detalhe.html'
    
    def get_queryset(self):
        return Processo.objects.select_related(
            'cliente',
            'cliente__usuario_responsavel',
            'tipo_processo',
            'tribunal',
            'usuario_responsavel'
        ).prefetch_related(
            'partes_envolvidas__parte',
            'documentos__tipo_documento',
            'movimentacoes__usuario',
            'prazos'
        )
```

##### 3. API Views Otimizadas
**Problema**: `clientes/api_views.py` - Serializers ineficientes
```python
# ANTES - Serializer sem otimização
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
```

**Solução Implementada**:
```python
# DEPOIS - Serializer otimizado com select_related
class ClienteSerializer(serializers.ModelSerializer):
    processos_count = serializers.SerializerMethodField()
    ultimo_processo = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'telefone', 'data_cadastro',
            'processos_count', 'ultimo_processo'
        ]
    
    def get_processos_count(self, obj):
        # Usa anotação para evitar query adicional
        return getattr(obj, 'processos_count', obj.processos.count())
    
    def get_ultimo_processo(self, obj):
        # Usa prefetch_related para evitar N+1
        processos = getattr(obj, 'processos_prefetched', obj.processos.all())
        ultimo = processos.first() if processos else None
        return ultimo.numero if ultimo else None

# ViewSet otimizada
class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        return Cliente.objects.select_related(
            'usuario_responsavel'
        ).prefetch_related(
            'processos'
        ).annotate(
            processos_count=Count('processos')
        ).order_by('-data_cadastro')
```

### Semana 2: Implementação de Cache Redis

#### ⚙️ Configuração do Redis

##### 1. Configuração no settings.py
```python
# settings.py - Configuração do Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'plataforma_juridica',
        'TIMEOUT': 300,  # 5 minutos padrão
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': 86400,  # 24 horas
    }
}

# Configuração de sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 horas
```

##### 2. Cache de Templates
```python
# settings.py - Cache de templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                # ... outros context processors
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

#### 🚀 Implementação de Cache Estratégico

##### 1. Cache em Views de Listagem
```python
# clientes/views.py - Cache implementado
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 5), name='dispatch')  # 5 minutos
class ClienteListView(ListView):
    model = Cliente
    template_name = 'clientes/lista.html'
    paginate_by = 20
    
    def get_queryset(self):
        # Cache da query otimizada
        cache_key = f'clientes_list_{self.request.user.id}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Cliente.objects.select_related(
                'usuario_responsavel'
            ).prefetch_related(
                'processos'
            ).annotate(
                processos_count=Count('processos')
            ).order_by('-data_cadastro')
            
            cache.set(cache_key, queryset, 60 * 5)  # 5 minutos
        
        return queryset
```

##### 2. Cache de Dados de Relatórios
```python
# relatorios/views.py - Cache de relatórios
from django.core.cache import cache
import hashlib

class RelatorioProcessosView(TemplateView):
    template_name = 'relatorios/processos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Gerar chave de cache baseada nos filtros
        filtros = self.request.GET.dict()
        cache_key = self._generate_cache_key('relatorio_processos', filtros)
        
        dados = cache.get(cache_key)
        if dados is None:
            dados = self._gerar_dados_relatorio(filtros)
            cache.set(cache_key, dados, 60 * 15)  # 15 minutos
        
        context['dados'] = dados
        return context
    
    def _generate_cache_key(self, prefix, filtros):
        """Gera chave de cache única baseada nos filtros"""
        filtros_str = str(sorted(filtros.items()))
        hash_obj = hashlib.md5(filtros_str.encode())
        return f'{prefix}_{self.request.user.id}_{hash_obj.hexdigest()}'
    
    def _gerar_dados_relatorio(self, filtros):
        """Gera dados do relatório com queries otimizadas"""
        return {
            'total_processos': Processo.objects.count(),
            'processos_por_status': Processo.objects.values('status').annotate(
                count=Count('id')
            ),
            'processos_por_mes': Processo.objects.extra(
                select={'mes': "DATE_FORMAT(data_cadastro, '%%Y-%%m')"}
            ).values('mes').annotate(count=Count('id')).order_by('mes')
        }
```

##### 3. Cache de Configurações do Sistema
```python
# core/utils.py - Cache de configurações
from django.core.cache import cache
from configuracoes.models import Configuracao

def get_configuracao(chave, default=None):
    """Obtém configuração com cache"""
    cache_key = f'config_{chave}'
    valor = cache.get(cache_key)
    
    if valor is None:
        try:
            config = Configuracao.objects.get(chave=chave)
            valor = config.valor
            cache.set(cache_key, valor, 60 * 60)  # 1 hora
        except Configuracao.DoesNotExist:
            valor = default
    
    return valor

def invalidar_cache_configuracao(chave):
    """Invalida cache de configuração específica"""
    cache_key = f'config_{chave}'
    cache.delete(cache_key)
```

##### 4. Invalidação Inteligente de Cache
```python
# core/signals.py - Invalidação automática
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from clientes.models import Cliente
from processos.models import Processo

@receiver([post_save, post_delete], sender=Cliente)
def invalidar_cache_cliente(sender, instance, **kwargs):
    """Invalida cache relacionado a clientes"""
    # Invalida cache da lista de clientes
    cache.delete_many([
        f'clientes_list_{instance.usuario_responsavel.id}',
        'relatorio_clientes_*',  # Pattern para relatórios
    ])

@receiver([post_save, post_delete], sender=Processo)
def invalidar_cache_processo(sender, instance, **kwargs):
    """Invalida cache relacionado a processos"""
    # Invalida cache do cliente relacionado
    if instance.cliente:
        cache.delete(f'clientes_list_{instance.cliente.usuario_responsavel.id}')
    
    # Invalida cache de relatórios
    cache.delete_pattern('relatorio_processos_*')
```

### Semana 3: Otimização de APIs e Validação

#### 🔧 Paginação Eficiente
```python
# core/pagination.py - Paginação otimizada
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class OptimizedPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })
```

#### 📊 Compressão de Resposta
```python
# settings.py - Middleware de compressão
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Adicionar no topo
    # ... outros middlewares
]

# Configuração de compressão
USE_GZIP = True
GZIP_CONTENT_TYPES = [
    'text/css',
    'text/javascript',
    'application/javascript',
    'application/json',
    'text/html',
    'text/plain',
    'text/xml',
    'application/xml',
]
```

## 📈 Resultados Esperados

### Métricas de Performance
- **Redução de Queries**: De 15-20 para 3-5 por request
- **Tempo de Resposta**: Redução de 40% (800ms → 480ms)
- **Cache Hit Ratio**: 80% em dados frequentemente acessados
- **Throughput**: Aumento de 100% (50 → 100 req/s)

### Benefícios Adicionais
- **Redução de Carga no Banco**: Menos queries simultâneas
- **Melhor Experiência do Usuário**: Páginas mais rápidas
- **Economia de Recursos**: Menor uso de CPU e memória
- **Escalabilidade**: Suporte a mais usuários simultâneos

## 🧪 Testes de Validação

### 1. Testes de Performance
```bash
# Executar testes de benchmark
pytest tests/performance/ -v --benchmark-only

# Análise de queries com Django Debug Toolbar
# Acessar: http://localhost:8001/__debug__/

# Profiling com Silk
# Acessar: http://localhost:8001/silk/
```

### 2. Testes de Cache
```python
# tests/test_cache.py
import pytest
from django.core.cache import cache
from django.test import TestCase
from clientes.models import Cliente

class CacheTestCase(TestCase):
    def test_cache_cliente_list(self):
        """Testa se o cache da lista de clientes funciona"""
        # Limpa cache
        cache.clear()
        
        # Primeira requisição (sem cache)
        response1 = self.client.get('/clientes/')
        
        # Segunda requisição (com cache)
        response2 = self.client.get('/clientes/')
        
        # Verifica se o cache foi utilizado
        self.assertEqual(response1.content, response2.content)
```

## 📋 Checklist de Implementação

### ✅ Concluído
- [x] Configuração do Django Debug Toolbar
- [x] Configuração do Django Silk
- [x] Instalação das dependências de desenvolvimento
- [x] Documentação da Fase 1

### 🔄 Em Andamento
- [ ] Análise detalhada de queries N+1
- [ ] Implementação de select_related/prefetch_related
- [ ] Configuração do Redis
- [ ] Implementação de cache estratégico

### ⏳ Pendente
- [ ] Otimização de serializers da API
- [ ] Implementação de paginação eficiente
- [ ] Testes de performance
- [ ] Validação das métricas
- [ ] Deploy em staging

## 🚨 Riscos e Mitigações

### Riscos Identificados
1. **Cache Stale**: Dados desatualizados no cache
   - **Mitigação**: Invalidação inteligente com signals

2. **Overhead de Memory**: Redis consumindo muita memória
   - **Mitigação**: TTL adequado e monitoramento

3. **Complexidade de Queries**: Queries muito complexas
   - **Mitigação**: Análise com EXPLAIN e otimização gradual

### Plano de Rollback
- Desabilitar cache via settings
- Reverter otimizações de queries problemáticas
- Monitoramento contínuo de performance

---

*Documento atualizado em: Janeiro 2025*
*Status: 🔄 Implementação em andamento*