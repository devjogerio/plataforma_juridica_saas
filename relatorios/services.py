from typing import Any, Dict, Tuple
from django.utils import timezone

from .models import TemplateRelatorio, ExecucaoRelatorio
from .views import _gerar_dados_relatorio


def executar_relatorio_service(template: TemplateRelatorio, usuario, parametros: Dict[str, Any]) -> Tuple[ExecucaoRelatorio, Dict[str, Any]]:
    """Executa um relatório a partir de um template, criando e atualizando a ExecucaoRelatorio"""
    execucao = ExecucaoRelatorio.objects.create(
        template=template,
        usuario=usuario,
        parametros_execucao=parametros,
        status='processando'
    )

    dados = _gerar_dados_relatorio(template, parametros, usuario)

    execucao.status = 'concluido'
    execucao.data_conclusao = timezone.now()
    execucao.total_registros = len(dados.get('registros', []))
    execucao.save()

    return execucao, dados