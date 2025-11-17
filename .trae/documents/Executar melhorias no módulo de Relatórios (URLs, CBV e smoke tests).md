## Objetivo
Aplicar as melhorias propostas nas reflexões: alinhar URLs e nomes de views, transformar a execução de relatório em CBV reutilizável, consolidar templates e criar smoke tests mínimos para evitar quebras transversais.

## Alterações Propostas
1. Alinhamento de URLs e Views
- Garantir que todas as rotas em `relatorios/urls.py` referenciem classes existentes em `relatorios/views.py` (ListaFiltrosView, Criar/Editar/Visualizar/TestarFiltro, ListaTemplates/ Criar/EditarTemplate, ListaExecucoes, ExecutarRelatorioView).
- Manter nomenclatura atual e padrões de CBVs (LoginRequiredMixin, context_object_name, template_name, `success_url`).

2. CBV para Execução de Relatórios
- Criar `ExecutarRelatorioView` (CBV) que recebe `template_id` na URL.
- Delegar a lógica de execução para uma função/método de serviço compartilhado (extrair de `executar_relatorio`): validação de permissões, construção de `ExecucaoRelatorio`, geração de dados e renderização/redirects.
- Manter consistência com templates existentes (`relatorios/executar.html`, `relatorios/resultado.html`).

3. Consolidação de Templates
- Verificar a existência dos templates referenciados nas views e ajustar nomes/pastas se necessário, mantendo a estrutura em `templates/relatorios/...`.
- Evitar duplicidades (ex.: `templates_list.html` vs `templates/templates_list.html`) e padronizar.

4. Smoke Tests do Módulo
- Criar testes simples em `relatorios/tests/` para:
  - Carregamento do URLConf sem `AttributeError`.
  - Resolução de rotas principais (dashboard, filtros, templates, execuções).
  - Respostas 200 para GET autenticado nas páginas listáveis.
  - Verificação de que `ExecutarRelatorioView` resolve e responde ao GET inicial.

## Segurança & Padrões
- Manter autenticação (`LoginRequiredMixin`/`IsAuthenticated`) e filtros por usuário quando aplicável.
- Não expor dados sensíveis; seguir variáveis via `.env` já existentes.
- Reutilizar forms e models atuais; aplicar SOLID separando a lógica de execução em serviço.

## Testes & Validação
- Rodar testes adicionados e os já existentes (foco nos erros anteriores) para garantir que não há regressões.
- Validar que o URLConf global carrega sem exceções.

## Fases
1. Ajustes de CBV/URLs (incluindo extração de serviço de execução).
2. Consolidação de templates e verificação visual mínima.
3. Criação de smoke tests.
4. Execução da suíte e correções pontuais se necessário.

Confirma implementar essas melhorias agora?