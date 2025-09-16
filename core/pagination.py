from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Paginação otimizada com informações adicionais de performance
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Retorna resposta paginada com metadados otimizados
        """
        return Response(OrderedDict([
            ('links', OrderedDict([
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link())
            ])),
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('has_next', self.page.has_next()),
            ('has_previous', self.page.has_previous()),
            ('results', data)
        ]))
    
    def get_page_size(self, request):
        """
        Determina o tamanho da página com validação
        """
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params[self.page_size_query_param])
                if page_size > 0:
                    return min(page_size, self.max_page_size)
            except (KeyError, ValueError):
                pass
        
        return self.page_size


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para a API"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Resposta personalizada com informações adicionais"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class LargeResultsSetPagination(PageNumberPagination):
    """Paginação para grandes conjuntos de dados"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        """Resposta personalizada com informações adicionais"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class SmallResultsSetPagination(PageNumberPagination):
    """Paginação para pequenos conjuntos de dados"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data):
        """Resposta personalizada com informações adicionais"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DocumentosPagination(PageNumberPagination):
    """Paginação específica para documentos"""
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Resposta com informações específicas para documentos"""
        # Calcular estatísticas dos documentos na página atual
        total_size = 0
        tipos_count = {}
        
        for doc in data:
            if 'tamanho_arquivo' in doc:
                total_size += doc.get('tamanho_arquivo', 0)
            
            tipo = doc.get('tipo', 'outros')
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_stats', {
                'total_size': total_size,
                'tipos_count': tipos_count,
                'items_count': len(data)
            }),
            ('results', data)
        ]))


class RelatoriosPagination(PageNumberPagination):
    """Paginação específica para relatórios"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Resposta com informações específicas para relatórios"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('export_available', True),  # Indica que os dados podem ser exportados
            ('results', data)
        ]))