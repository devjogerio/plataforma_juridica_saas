# Plataforma Jurídica SaaS

Plataforma completa de gestão de processos jurídicos desenvolvida com Django, seguindo os princípios de Clean Architecture e padrões de desenvolvimento modernos.

## 🚀 Funcionalidades

### Módulos Principais
- **Gestão de Processos**: Cadastro, andamentos, prazos e controle completo
- **Gestão de Clientes**: CRM básico com histórico de interações
- **Gestão de Documentos**: Upload seguro com controle de versões
- **Módulo Financeiro**: Honorários, despesas e controle de pagamentos
- **Relatórios e Dashboards**: Analytics e relatórios personalizáveis
- **Sistema de Usuários**: RBAC com diferentes perfis de acesso
- **Auditoria**: Log completo de ações para compliance

### Tecnologias Utilizadas
- **Backend**: Django 4.2+ com Python 3.11+
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **API**: Django REST Framework
- **Cache**: Redis
- **Task Queue**: Celery
- **Frontend**: Django Templates + Bootstrap 5
- **Autenticação**: Sistema personalizado com JWT

## 📋 Pré-requisitos

- Python 3.11+
- Node.js 18+ (para assets frontend)
- PostgreSQL (para produção)
- Redis (para cache e Celery)

## 🛠️ Instalação e Configuração

### 1. Clone o repositório
```bash
git clone <repository-url>
cd plataforma_juridica_saas
```

### 2. Crie e ative o ambiente virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Execute as migrações
```bash
python manage.py migrate
```

### 6. Crie um superusuário
```bash
python create_superuser.py
# ou
python manage.py createsuperuser
```

### 7. Inicie o servidor de desenvolvimento
```bash
python manage.py runserver
```

A aplicação estará disponível em: http://127.0.0.1:8000/

## 🔐 Acesso Inicial

**Administrador:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@plataformajuridica.com`

**Admin Django:** http://127.0.0.1:8000/admin/

## 📁 Estrutura do Projeto

```
plataforma_juridica_saas/
├── plataforma_juridica/          # Configurações principais
│   ├── settings.py              # Configurações Django
│   ├── urls.py                  # URLs principais
│   └── wsgi.py                  # WSGI config
├── core/                        # App core (middleware, utils)
├── usuarios/                    # Gestão de usuários e permissões
├── clientes/                    # Gestão de clientes e partes
├── processos/                   # Gestão de processos jurídicos
├── documentos/                  # Gestão de documentos
├── financeiro/                  # Controle financeiro
├── relatorios/                  # Relatórios e dashboards
├── configuracoes/               # Configurações do sistema
├── static/                      # Arquivos estáticos
├── media/                       # Uploads de usuários
├── logs/                        # Logs da aplicação
└── requirements.txt             # Dependências Python
```

## 🏗️ Arquitetura

O projeto segue os princípios da **Clean Architecture**:

- **Entities**: Modelos de domínio (models.py)
- **Use Cases**: Lógica de negócio (services.py)
- **Interface Adapters**: Controllers (views.py) e Presenters (serializers.py)
- **Frameworks & Drivers**: Django, PostgreSQL, etc.

### Padrões Implementados
- **Repository Pattern**: Para acesso a dados
- **Service Layer**: Para lógica de negócio
- **CQRS**: Separação de comandos e consultas
- **Event Sourcing**: Para auditoria

## 🔒 Segurança

- Autenticação JWT
- RBAC (Role-Based Access Control)
- Middleware de auditoria
- Validação de entrada
- Proteção CSRF
- Headers de segurança

## 📊 Monitoramento

- Logs estruturados
- Health checks
- Métricas de performance
- Auditoria completa de ações

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=.

# Executar testes específicos
pytest usuarios/tests/
```

## 🚀 Deploy

### Produção com Docker
```bash
# Build da imagem
docker build -t plataforma-juridica .

# Executar com docker-compose
docker-compose up -d
```

### Variáveis de Ambiente (Produção)
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgres://user:pass@localhost:5432/plataforma_juridica
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com
```

## 📝 API Documentation

A documentação da API está disponível em:
- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte técnico, entre em contato:
- Email: suporte@plataformajuridica.com
- Issues: GitHub Issues

## 🔄 Changelog

### v1.0.0 (2024-12-19)
- ✨ Implementação inicial da plataforma
- 🏗️ Arquitetura Clean Architecture
- 🔐 Sistema de autenticação e autorização
- 📊 Módulos principais implementados
- 🧪 Testes unitários e de integração
- 📚 Documentação completa