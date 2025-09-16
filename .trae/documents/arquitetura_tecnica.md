# Documentação de Arquitetura Técnica - Plataforma Jurídica

## 1. Design da Arquitetura

```mermaid
graph TD
    A[Navegador do Usuário] --> B[Frontend Django Templates]
    B --> C[Django Views/Controllers]
    C --> D[Django Models/ORM]
    C --> E[Django REST Framework API]
    D --> F[PostgreSQL Database]
    C --> G[Celery Task Queue]
    G --> H[Redis Cache/Broker]
    C --> I[Sistema de Arquivos]
    
    subgraph "Camada de Apresentação"
        B
    end
    
    subgraph "Camada de Aplicação"
        C
        E
    end
    
    subgraph "Camada de Domínio"
        D
    end
    
    subgraph "Camada de Infraestrutura"
        F
        H
        I
    end
    
    subgraph "Processamento Assíncrono"
        G
    end
```

## 2. Descrição das Tecnologias

* **Backend**: Django 4.2+ com Python 3.11+

* **Banco de Dados**: PostgreSQL 15+ (produção), SQLite (desenvolvimento)

* **API**: Django REST Framework 3.14+

* **Cache/Broker**: Redis 7.0+

* **Task Queue**: Celery 5.3+

* **Frontend**: Django Templates + Bootstrap 5 + JavaScript ES6+

* **Autenticação**: Django Authentication System

* **Armazenamento**: Sistema de arquivos local (desenvolvimento), AWS S3 (produção)

## 3. Definições de Rotas

| Rota                          | Propósito                                  |
| ----------------------------- | ------------------------------------------ |
| `/`                           | Dashboard principal com KPIs e visão geral |
| `/login/`                     | Página de autenticação de usuários         |
| `/logout/`                    | Logout e redirecionamento                  |
| `/dashboard/`                 | Dashboard principal pós-login              |
| `/processos/`                 | Lista de processos com filtros             |
| `/processos/novo/`            | Formulário de cadastro de novo processo    |
| `/processos/<id>/`            | Detalhes de processo específico            |
| `/processos/<id>/andamentos/` | Andamentos de um processo                  |
| `/processos/<id>/documentos/` | Documentos de um processo                  |
| `/clientes/`                  | Lista de clientes                          |
| `/clientes/novo/`             | Cadastro de novo cliente                   |
| `/clientes/<id>/`             | Perfil detalhado do cliente                |
| `/financeiro/`                | Dashboard financeiro                       |
| `/financeiro/honorarios/`     | Gestão de honorários                       |
| `/financeiro/despesas/`       | Controle de despesas                       |
| `/relatorios/`                | Centro de relatórios                       |
| `/configuracoes/`             | Configurações do sistema                   |
| `/api/v1/`                    | Base da API REST                           |

## 4. Definições da API

### 4.1 API Principal

**Autenticação de usuários**

```
POST /api/v1/auth/login/
```

Request:

| Parâmetro | Tipo   | Obrigatório | Descrição                |
| --------- | ------ | ----------- | ------------------------ |
| username  | string | true        | Nome de usuário ou email |
| password  | string | true        | Senha do usuário         |

Response:

| Parâmetro   | Tipo   | Descrição                 |
| ----------- | ------ | ------------------------- |
| token       | string | Token de autenticação JWT |
| user        | object | Dados básicos do usuário  |
| permissions | array  | Lista de permissões       |

Exemplo:

```json
{
  "username": "advogado@escritorio.com",
  "password": "senha123"
}
```

**Gestão de Processos**

```
GET /api/v1/processos/
POST /api/v1/processos/
GET /api/v1/processos/{id}/
PUT /api/v1/processos/{id}/
DELETE /api/v1/processos/{id}/
```

**Gestão de Clientes**

```
GET /api/v1/clientes/
POST /api/v1/clientes/
GET /api/v1/clientes/{id}/
PUT /api/v1/clientes/{id}/
```

**Andamentos Processuais**

```
GET /api/v1/processos/{id}/andamentos/
POST /api/v1/processos/{id}/andamentos/
```

**Upload de Documentos**

```
POST /api/v1/processos/{id}/documentos/
```

Request:

| Parâmetro | Tipo   | Obrigatório | Descrição              |
| --------- | ------ | ----------- | ---------------------- |
| arquivo   | file   | true        | Arquivo a ser enviado  |
| tipo      | string | true        | Tipo do documento      |
| descricao | string | false       | Descrição do documento |

## 5. Arquitetura do Servidor

```mermaid
graph TD
    A[Cliente/Frontend] --> B[Camada de Controllers]
    B --> C[Camada de Services]
    C --> D[Camada de Repositories]
    D --> E[(Banco de Dados)]
    
    subgraph Servidor
        B
        C
        D
    end
    
    subgraph "Clean Architecture Layers"
        F[Entities - Regras de Negócio]
        G[Use Cases - Lógica de Aplicação]
        H[Interface Adapters - Controllers/Presenters]
        I[Frameworks & Drivers - Django/PostgreSQL]
    end
```

## 6. Modelo de Dados

### 6.1 Definição do Modelo de Dados

```mermaid
erDiagram
    USUARIO ||--o{ PROCESSO : cria
    CLIENTE ||--o{ PROCESSO : possui
    PROCESSO ||--o{ ANDAMENTO : tem
    PROCESSO ||--o{ DOCUMENTO : contem
    PROCESSO ||--o{ PRAZO : possui
    PROCESSO ||--o{ HONORARIO : gera
    PROCESSO ||--o{ DESPESA : tem
    CLIENTE ||--o{ PARTE_ENVOLVIDA : relaciona
    PROCESSO ||--o{ PARTE_ENVOLVIDA : envolve
    USUARIO ||--o{ PERMISSAO : possui
    
    USUARIO {
        uuid id PK
        string username
        string email
        string password_hash
        string first_name
        string last_name
        string tipo_usuario
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    CLIENTE {
        uuid id PK
        string tipo_pessoa
        string nome_razao_social
        string cpf_cnpj
        string rg_ie
        string email
        string telefone
        string endereco
        string cidade
        string estado
        string cep
        text observacoes
        datetime created_at
        datetime updated_at
    }
    
    PROCESSO {
        uuid id PK
        string numero_processo
        string tipo_processo
        string area_direito
        string status
        decimal valor_causa
        string comarca_tribunal
        string vara_orgao
        date data_inicio
        date data_encerramento
        text observacoes
        uuid cliente_id FK
        uuid usuario_responsavel_id FK
        datetime created_at
        datetime updated_at
    }
    
    ANDAMENTO {
        uuid id PK
        uuid processo_id FK
        date data_andamento
        text descricao
        string tipo_andamento
        uuid usuario_id FK
        datetime created_at
    }
    
    DOCUMENTO {
        uuid id PK
        uuid processo_id FK
        string nome_arquivo
        string tipo_documento
        string caminho_arquivo
        integer tamanho_arquivo
        string hash_arquivo
        text descricao
        uuid usuario_upload_id FK
        datetime created_at
    }
    
    PRAZO {
        uuid id PK
        uuid processo_id FK
        string tipo_prazo
        date data_limite
        text descricao
        boolean cumprido
        date data_cumprimento
        uuid usuario_responsavel_id FK
        datetime created_at
    }
    
    PARTE_ENVOLVIDA {
        uuid id PK
        uuid processo_id FK
        string nome
        string tipo_envolvimento
        string cpf_cnpj
        string email
        string telefone
        text observacoes
        datetime created_at
    }
    
    HONORARIO {
        uuid id PK
        uuid processo_id FK
        uuid cliente_id FK
        string tipo_cobranca
        decimal valor
        decimal percentual_exito
        string status_pagamento
        date data_vencimento
        date data_pagamento
        text observacoes
        datetime created_at
    }
    
    DESPESA {
        uuid id PK
        uuid processo_id FK
        string tipo_despesa
        decimal valor
        date data_despesa
        text descricao
        string status_reembolso
        datetime created_at
    }
    
    PERMISSAO {
        uuid id PK
        uuid usuario_id FK
        string modulo
        string acao
        boolean permitido
        datetime created_at
    }
```

### 6.2 Linguagem de Definição de Dados (DDL)

**Tabela de Usuários**

```sql
-- Criar tabela de usuários
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    tipo_usuario VARCHAR(20) DEFAULT 'advogado' CHECK (tipo_usuario IN ('administrador', 'advogado', 'estagiario', 'cliente')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de clientes
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_pessoa VARCHAR(2) NOT NULL CHECK (tipo_pessoa IN ('PF', 'PJ')),
    nome_razao_social VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18) UNIQUE NOT NULL,
    rg_ie VARCHAR(20),
    email VARCHAR(254),
    telefone VARCHAR(20),
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de processos
CREATE TABLE processos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_processo VARCHAR(50) UNIQUE NOT NULL,
    tipo_processo VARCHAR(50) NOT NULL,
    area_direito VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'suspenso', 'encerrado')),
    valor_causa DECIMAL(15,2),
    comarca_tribunal VARCHAR(200),
    vara_orgao VARCHAR(200),
    data_inicio DATE NOT NULL,
    data_encerramento DATE,
    observacoes TEXT,
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    usuario_responsavel_id UUID NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índices para otimização
CREATE INDEX idx_processos_cliente_id ON processos(cliente_id);
CREATE INDEX idx_processos_usuario_responsavel ON processos(usuario_responsavel_id);
CREATE INDEX idx_processos_status ON processos(status);
CREATE INDEX idx_processos_data_inicio ON processos(data_inicio DESC);

-- Dados iniciais
INSERT INTO usuarios (username, email, password_hash, first_name, last_name, tipo_usuario)
VALUES 
    ('admin', 'admin@plataformajuridica.com', 'pbkdf2_sha256$hash', 'Administrador', 'Sistema', 'administrador'),
    ('advogado1', 'advogado@escritorio.com', 'pbkdf2_sha256$hash', 'João', 'Silva', 'advogado');
```

