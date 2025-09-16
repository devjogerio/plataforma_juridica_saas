from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()

# Mapeamento de URLs para títulos e ícones
BREADCRUMB_MAP = {
    # Core
    'core:dashboard': {'title': 'Dashboard', 'icon': 'fas fa-tachometer-alt'},
    'core:login': {'title': 'Login', 'icon': 'fas fa-sign-in-alt'},
    
    # Processos
    'processos:lista': {'title': 'Processos', 'icon': 'fas fa-folder-open'},
    'processos:criar': {'title': 'Novo Processo', 'icon': 'fas fa-plus'},
    'processos:detalhe': {'title': 'Detalhes do Processo', 'icon': 'fas fa-eye'},
    'processos:editar': {'title': 'Editar Processo', 'icon': 'fas fa-edit'},
    'processos:andamentos': {'title': 'Andamentos', 'icon': 'fas fa-list'},
    'processos:prazos': {'title': 'Prazos', 'icon': 'fas fa-calendar'},
    
    # Clientes
    'clientes:lista': {'title': 'Clientes', 'icon': 'fas fa-users'},
    'clientes:criar': {'title': 'Novo Cliente', 'icon': 'fas fa-user-plus'},
    'clientes:detalhe': {'title': 'Detalhes do Cliente', 'icon': 'fas fa-user'},
    'clientes:editar': {'title': 'Editar Cliente', 'icon': 'fas fa-user-edit'},
    
    # Documentos
    'documentos:lista': {'title': 'Documentos', 'icon': 'fas fa-file-alt'},
    'documentos:upload': {'title': 'Upload de Documento', 'icon': 'fas fa-upload'},
    'documentos:detalhe': {'title': 'Detalhes do Documento', 'icon': 'fas fa-file'},
    
    # Financeiro
    'financeiro:dashboard': {'title': 'Financeiro', 'icon': 'fas fa-dollar-sign'},
    'financeiro:honorarios': {'title': 'Honorários', 'icon': 'fas fa-money-bill'},
    'financeiro:despesas': {'title': 'Despesas', 'icon': 'fas fa-receipt'},
    'financeiro:criar_honorario': {'title': 'Novo Honorário', 'icon': 'fas fa-plus'},
    
    # Relatórios
    'relatorios:dashboard': {'title': 'Relatórios', 'icon': 'fas fa-chart-bar'},
    'relatorios:processos': {'title': 'Relatório de Processos', 'icon': 'fas fa-folder'},
    'relatorios:clientes': {'title': 'Relatório de Clientes', 'icon': 'fas fa-users'},
    'relatorios:financeiro': {'title': 'Relatório Financeiro', 'icon': 'fas fa-chart-line'},
    
    # Configurações
    'configuracoes:dashboard': {'title': 'Configurações', 'icon': 'fas fa-cogs'},
    'configuracoes:tipos_processo': {'title': 'Tipos de Processo', 'icon': 'fas fa-folder-open'},
    'configuracoes:areas_direito': {'title': 'Áreas do Direito', 'icon': 'fas fa-balance-scale'},
    'configuracoes:status_processo': {'title': 'Status de Processo', 'icon': 'fas fa-tags'},
    'configuracoes:modelos_documentos': {'title': 'Modelos de Documento', 'icon': 'fas fa-file-alt'},
    'configuracoes:sistema': {'title': 'Sistema', 'icon': 'fas fa-server'},
    
    # Usuários
    'usuarios:lista': {'title': 'Usuários', 'icon': 'fas fa-users'},
    'usuarios:perfil': {'title': 'Meu Perfil', 'icon': 'fas fa-user'},
    'usuarios:editar_perfil': {'title': 'Editar Perfil', 'icon': 'fas fa-user-edit'},
    'usuarios:preferencias': {'title': 'Preferências', 'icon': 'fas fa-sliders-h'},
    'usuarios:permissoes': {'title': 'Permissões', 'icon': 'fas fa-shield-alt'},
}

# Hierarquia de navegação
NAVIGATION_HIERARCHY = {
    # Processos
    'processos:criar': ['core:dashboard', 'processos:lista'],
    'processos:detalhe': ['core:dashboard', 'processos:lista'],
    'processos:editar': ['core:dashboard', 'processos:lista', 'processos:detalhe'],
    'processos:andamentos': ['core:dashboard', 'processos:lista', 'processos:detalhe'],
    'processos:prazos': ['core:dashboard', 'processos:lista'],
    
    # Clientes
    'clientes:criar': ['core:dashboard', 'clientes:lista'],
    'clientes:detalhe': ['core:dashboard', 'clientes:lista'],
    'clientes:editar': ['core:dashboard', 'clientes:lista', 'clientes:detalhe'],
    
    # Documentos
    'documentos:upload': ['core:dashboard', 'documentos:lista'],
    'documentos:detalhe': ['core:dashboard', 'documentos:lista'],
    
    # Financeiro
    'financeiro:honorarios': ['core:dashboard', 'financeiro:dashboard'],
    'financeiro:despesas': ['core:dashboard', 'financeiro:dashboard'],
    'financeiro:criar_honorario': ['core:dashboard', 'financeiro:dashboard', 'financeiro:honorarios'],
    
    # Relatórios
    'relatorios:processos': ['core:dashboard', 'relatorios:dashboard'],
    'relatorios:clientes': ['core:dashboard', 'relatorios:dashboard'],
    'relatorios:financeiro': ['core:dashboard', 'relatorios:dashboard'],
    
    # Configurações
    'configuracoes:tipos_processo': ['core:dashboard', 'configuracoes:dashboard'],
    'configuracoes:areas_direito': ['core:dashboard', 'configuracoes:dashboard'],
    'configuracoes:status_processo': ['core:dashboard', 'configuracoes:dashboard'],
    'configuracoes:modelos_documentos': ['core:dashboard', 'configuracoes:dashboard'],
    'configuracoes:sistema': ['core:dashboard', 'configuracoes:dashboard'],
    
    # Usuários
    'usuarios:editar_perfil': ['core:dashboard', 'usuarios:perfil'],
    'usuarios:preferencias': ['core:dashboard', 'usuarios:perfil'],
}


@register.simple_tag(takes_context=True)
def breadcrumbs(context, custom_items=None):
    """
    Gera breadcrumbs automaticamente baseado na URL atual.
    
    Uso:
    {% load breadcrumbs %}
    {% breadcrumbs %}
    
    Ou com itens customizados:
    {% breadcrumbs "Dashboard,/|Processos,/processos/|Novo Processo" %}
    """
    request = context['request']
    
    if custom_items:
        return _render_custom_breadcrumbs(custom_items)
    
    # Obter o nome da URL atual
    current_url_name = None
    if hasattr(request, 'resolver_match') and request.resolver_match:
        current_url_name = f"{request.resolver_match.namespace}:{request.resolver_match.url_name}" if request.resolver_match.namespace else request.resolver_match.url_name
    
    if not current_url_name or current_url_name not in BREADCRUMB_MAP:
        return ''
    
    # Construir hierarquia
    hierarchy = NAVIGATION_HIERARCHY.get(current_url_name, ['core:dashboard'])
    hierarchy.append(current_url_name)
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique_hierarchy = []
    for item in hierarchy:
        if item not in seen:
            seen.add(item)
            unique_hierarchy.append(item)
    
    # Gerar HTML dos breadcrumbs
    breadcrumb_items = []
    
    for i, url_name in enumerate(unique_hierarchy):
        if url_name not in BREADCRUMB_MAP:
            continue
            
        config = BREADCRUMB_MAP[url_name]
        title = config['title']
        icon = config['icon']
        
        is_last = (i == len(unique_hierarchy) - 1)
        
        if is_last:
            # Item atual (não clicável)
            breadcrumb_items.append(
                format_html(
                    '<li class="breadcrumb-item active" aria-current="page">'
                    '<i class="{} me-1"></i>{}'
                    '</li>',
                    icon, title
                )
            )
        else:
            # Item clicável
            try:
                url = reverse(url_name)
                breadcrumb_items.append(
                    format_html(
                        '<li class="breadcrumb-item">'
                        '<a href="{}"><i class="{} me-1"></i>{}</a>'
                        '</li>',
                        url, icon, title
                    )
                )
            except NoReverseMatch:
                # Se não conseguir resolver a URL, adiciona sem link
                breadcrumb_items.append(
                    format_html(
                        '<li class="breadcrumb-item">'
                        '<i class="{} me-1"></i>{}'
                        '</li>',
                        icon, title
                    )
                )
    
    if not breadcrumb_items:
        return ''
    
    return mark_safe(
        '<nav aria-label="breadcrumb" class="mb-4">'
        '<ol class="breadcrumb">'
        ''.join(breadcrumb_items) +
        '</ol>'
        '</nav>'
    )


def _render_custom_breadcrumbs(custom_items):
    """
    Renderiza breadcrumbs customizados.
    Formato: "Título1,/url1/|Título2,/url2/|Título3"
    """
    items = custom_items.split('|')
    breadcrumb_items = []
    
    for i, item in enumerate(items):
        if ',' in item:
            title, url = item.split(',', 1)
            is_last = (i == len(items) - 1)
            
            if is_last or not url.strip():
                # Item atual (não clicável)
                breadcrumb_items.append(
                    format_html(
                        '<li class="breadcrumb-item active" aria-current="page">'
                        '{}'
                        '</li>',
                        title.strip()
                    )
                )
            else:
                # Item clicável
                breadcrumb_items.append(
                    format_html(
                        '<li class="breadcrumb-item">'
                        '<a href="{}">{}</a>'
                        '</li>',
                        url.strip(), title.strip()
                    )
                )
        else:
            # Item sem URL (atual)
            breadcrumb_items.append(
                format_html(
                    '<li class="breadcrumb-item active" aria-current="page">'
                    '{}'
                    '</li>',
                    item.strip()
                )
            )
    
    if not breadcrumb_items:
        return ''
    
    return mark_safe(
        '<nav aria-label="breadcrumb" class="mb-4">'
        '<ol class="breadcrumb">'
        ''.join(breadcrumb_items) +
        '</ol>'
        '</nav>'
    )


@register.simple_tag
def breadcrumb_item(title, url=None, icon=None, active=False):
    """
    Cria um item de breadcrumb individual.
    
    Uso:
    {% breadcrumb_item "Dashboard" "/" "fas fa-home" %}
    {% breadcrumb_item "Processos" active=True %}
    """
    icon_html = f'<i class="{icon} me-1"></i>' if icon else ''
    
    if active or not url:
        return format_html(
            '<li class="breadcrumb-item active" aria-current="page">'
            '{}{}'
            '</li>',
            icon_html, title
        )
    else:
        return format_html(
            '<li class="breadcrumb-item">'
            '<a href="{}">{}{}</a>'
            '</li>',
            url, icon_html, title
        )


@register.inclusion_tag('core/breadcrumbs.html', takes_context=True)
def render_breadcrumbs(context, custom_items=None):
    """
    Template tag de inclusão para renderizar breadcrumbs.
    """
    request = context['request']
    
    # Obter breadcrumbs
    breadcrumbs_html = breadcrumbs(context, custom_items)
    
    return {
        'breadcrumbs_html': breadcrumbs_html,
        'request': request
    }