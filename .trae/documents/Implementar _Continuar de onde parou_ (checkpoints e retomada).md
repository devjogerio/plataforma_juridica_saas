## Contexto do Projeto
- Stack atual: Django + DRF, Redis (cache/sessões), Celery, PostgreSQL; templates com JS simples e uso pontual de `localStorage`.
- Não há autosave/retomada implementados; existem utilitários de cache em `core/cache_utils.py` e sessões em Redis prontos para uso.

## Objetivo
- Permitir que usuários retomem formulários e processos exatamente do ponto interrompido, com salvamentos automáticos (checkpoints), metadados e função de retomada confiável, segura e multi-dispositivo.

## Pilares da Implementação
1. Persistência de rascunhos temporários em Redis (rápido, TTL curto).
2. Versões opcionais de longo prazo em banco (PostgreSQL) via `JSONField` quando necessário (ex.: etapas longas de processos).
3. Endpoints REST para salvar/carregar/excluir rascunhos com autenticação e limites.
4. Autosave no front-end com debounce, detecção offline e sincronização quando online.
5. Integridade e segurança: validação de permissões, HMAC server-side e limites de tamanho/frequência.

## Modelo de Dados (leve)
- Chave de rascunho: `user_id:form_slug:object_id`.
- Payload: `{ data: FormDataParcial, fieldsStatus, step, timestamp, version, schemaVersion }`.
- Metadados: `{ ttl, source: 'web', userAgent, ip_masked }` (sem dados sensíveis).
- Versões persistentes (opcional): tabela `DraftVersion` com `user`, `form_slug`, `object_id`, `payload (JSONField)`, `created_at`, `hash`.

## Backend
- Serviço de rascunhos (novo módulo de domínio):
  - `save_draft(user, form_slug, object_id, payload, ttl)` usando `core/cache_utils.CacheManager` (Redis).
  - `load_draft(user, form_slug, object_id)` com verificação de integridade e permissão.
  - `delete_draft(user, form_slug, object_id)` para limpeza após submissão.
  - HMAC do payload com `SECRET_KEY` para detectar corrupção/tampering.
- DRF Endpoints (`api/v1/forms/drafts/`):
  - `POST /save` (body: `form_slug`, `object_id`, `payload`) – throttle, autenticação JWT/Session.
  - `GET /load` (query: `form_slug`, `object_id`) – retorna último checkpoint.
  - `DELETE /clear` – remove rascunho.
- Regras e limites:
  - TTL via env (ex.: 1200s dev/prod; menor em test).
  - Max payload (ex.: 64–128KB), rate limit (ex.: 10 req/min por usuário).
  - Permissões: apenas autor do rascunho acessa.

## Front-end (templates)
- Módulo JS discreto em páginas de formulário (`processos`, `clientes`, `financeiro`):
  - Captura eventos `input`/`blur` com debounce (ex.: 1500ms) e chama `POST /save`.
  - Ao carregar, chama `GET /load` e aplica `payload.data` aos campos (mantendo foco/step).
  - Offline-first: guarda em `localStorage` e envia ao servidor quando `navigator.onLine`.
  - UX: banner "Rascunho restaurado" com botão desfazer e indicação de próximo campo/etapa.

## Autosave e Checkpoints
- Intervalo automático (fallback de timer) além de eventos – configurável via env.
- Limpeza automática do rascunho ao concluir/submeter o formulário.
- Logs de auditoria via `AuditMiddleware` para operações save/load/clear.

## Retomada
- Na abertura de um formulário:
  1) Buscar rascunho por chave.
  2) Validar `schemaVersion` e `hash`.
  3) Restaurar `data`, marcar campos preenchidos, posicionar no `step`.
  4) Exibir painel indicando ponto de continuação.

## Integridade e Segurança
- HMAC do payload usando `SECRET_KEY` (não expor em cliente).
- Sanitização/validação do `payload` contra schema por `form_slug`.
- Sem dados sensíveis em `localStorage`.
- Limitar tamanho, frequência e vida útil (TTL) de rascunhos.

## Testes
- Unidade (serviço): salvar/carregar/excluir, TTL, hash inválido, permissões.
- Integração (DRF): autenticação, throttle, limites, restauração em formulários `processos`/`clientes`.
- E2E leve (Django Test Client + fixtures): preencher, interromper, retomar, submeter e limpar.
- Testes de offline: simular queda de rede e sincronização posterior.

## Variáveis de Ambiente (.env.example)
- `CHECKPOINT_TTL_SECONDS=1200`
- `AUTOSAVE_DEBOUNCE_MS=1500`
- `CHECKPOINT_MAX_PAYLOAD_KB=128`
- `CHECKPOINT_RATE_LIMIT_PER_MINUTE=10`
- `CHECKPOINT_STORAGE=redis` (ou `db` para versões persistentes)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (já existentes; usados se necessário para tarefas de limpeza em lote)

## Observabilidade
- Métricas: contagem de saves/loads/clears por usuário/form.
- Logs estruturados: sucesso/erro, tamanho de payload, latência.
- Alertas para taxas anômalas.

## Fases de Entrega
1. Backend serviço + endpoints (save/load/clear) com testes de unidade/integr.
2. Front-end autosave/debounce + restauração básica em `processos`.
3. Extensão para `clientes`/`financeiro` + UX de retomada.
4. Hardening: limites, HMAC, observabilidade, testes offline.
5. (Opcional) Versões persistentes em DB para fluxos longos.

## Riscos e Mitigações
- Conflitos de versão: usar `schemaVersion`; migrar rascunhos quando necessário.
- Volume no Redis: TTL curto, limpeza pós-submit, limites por usuário.
- Privacidade: nunca gravar dados sensíveis em `localStorage`; apenas servidor.

Confirme para avançarmos com a implementação seguindo estas fases e parâmetros.