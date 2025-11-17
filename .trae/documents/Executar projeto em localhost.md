## Objetivo
Subir o servidor de desenvolvimento no localhost com validação mínima dos endpoints e logs, seguindo as práticas do projeto.

## Pré-condições
- Verificar se `.env` existe e contém ao menos `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS=localhost,127.0.0.1` e variáveis de Redis/Celery conforme `.env.example`.
- Dependências instaladas (`pip install -r requirements.txt`) e virtualenv ativo.

## Passos
1. Migrar banco de dados
- Executar `python manage.py migrate` para aplicar migrações.

2. Iniciar servidor
- Executar `python manage.py runserver 8000` (não bloqueante).
- Monitorar logs iniciais do terminal e garantir ausência de erros.

3. Abrir preview
- Expor a URL `http://localhost:8000/` e validar acesso.

4. Verificação rápida
- Chamar `GET /api/v1/status/` e verificar resposta JSON de saúde da API.
- Opcional: validar `GET /api/v1/forms/drafts/load` autenticado quando apropriado.

5. Observação de segurança
- Não alterar `.env` sem confirmação; usar exclusivamente variáveis documentadas.

## Saída Esperada
- Servidor rodando em `http://localhost:8000/`.
- Endpoint de status respondendo com `200` e payload esperado.

Confirma execução agora?