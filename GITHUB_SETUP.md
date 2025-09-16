# Configuração do GitHub para Plataforma Jurídica SaaS

## 📋 Pré-requisitos

1. **Git instalado** no seu sistema
2. **Conta no GitHub** criada
3. **SSH configurado** (recomendado) ou usar HTTPS

## 🔧 Comandos para Configuração Inicial

### 1. Inicializar o repositório Git local

```bash
# Navegar para o diretório do projeto
cd f:\plataforma_juridica_saas

# Inicializar o repositório Git
git init

# Configurar informações do usuário (se ainda não configurado globalmente)
git config user.name "Seu Nome"
git config user.email "seu.email@exemplo.com"
```

### 2. Criar o repositório no GitHub

**Opção A: Via GitHub CLI (gh)**
```bash
# Instalar GitHub CLI se não tiver: https://cli.github.com/
# Fazer login
gh auth login

# Criar repositório público
gh repo create plataforma_juridica_saas --public --description "Plataforma SaaS completa para gestão de escritórios de advocacia"

# Ou criar repositório privado
gh repo create plataforma_juridica_saas --private --description "Plataforma SaaS completa para gestão de escritórios de advocacia"
```

**Opção B: Via Interface Web**
1. Acesse [GitHub](https://github.com)
2. Clique em "New repository"
3. Nome: `plataforma_juridica_saas`
4. Descrição: "Plataforma SaaS completa para gestão de escritórios de advocacia"
5. Escolha público ou privado
6. **NÃO** marque "Initialize with README" (já temos os arquivos)
7. Clique em "Create repository"

### 3. Conectar repositório local ao GitHub

```bash
# Adicionar origem remota (substitua 'seu-usuario' pelo seu username)
git remote add origin https://github.com/seu-usuario/plataforma_juridica_saas.git

# Ou usando SSH (recomendado se configurado)
git remote add origin git@github.com:seu-usuario/plataforma_juridica_saas.git

# Verificar se a origem foi adicionada corretamente
git remote -v
```

### 4. Preparar e enviar o código inicial

```bash
# Adicionar todos os arquivos ao staging
git add .

# Verificar status dos arquivos
git status

# Fazer o primeiro commit
git commit -m "feat: configuração inicial do projeto plataforma jurídica SaaS

- Adicionado package.json com dependências principais
- Configurado .gitignore para Node.js e arquivos sensíveis
- Criado README.md com documentação completa
- Adicionado .env.example com variáveis de ambiente
- Estrutura base para aplicação SaaS jurídica"

# Renomear branch principal para 'main' (padrão atual)
git branch -M main

# Enviar código para o GitHub
git push -u origin main
```

## 🔄 Comandos para Desenvolvimento Contínuo

### Workflow diário de desenvolvimento

```bash
# Verificar status atual
git status

# Adicionar arquivos modificados
git add .
# Ou adicionar arquivos específicos
git add src/components/NovoComponente.jsx

# Fazer commit com mensagem descritiva
git commit -m "feat: implementar autenticação de usuários"

# Enviar para o GitHub
git push origin main
```

### Trabalhando com branches (recomendado)

```bash
# Criar e mudar para nova branch
git checkout -b feature/sistema-clientes

# Ou criar branch sem mudar
git branch feature/sistema-clientes
git checkout feature/sistema-clientes

# Fazer commits na branch
git add .
git commit -m "feat: adicionar CRUD de clientes"

# Enviar branch para o GitHub
git push -u origin feature/sistema-clientes

# Voltar para main
git checkout main

# Fazer merge da branch (após aprovação)
git merge feature/sistema-clientes

# Deletar branch local após merge
git branch -d feature/sistema-clientes

# Deletar branch remota
git push origin --delete feature/sistema-clientes
```

## 📝 Convenções de Commit

Use o padrão **Conventional Commits**:

```bash
# Novas funcionalidades
git commit -m "feat: adicionar sistema de agendamento"

# Correções de bugs
git commit -m "fix: corrigir erro na validação de CPF"

# Documentação
git commit -m "docs: atualizar README com instruções de deploy"

# Refatoração
git commit -m "refactor: reorganizar estrutura de pastas"

# Testes
git commit -m "test: adicionar testes para módulo de processos"

# Configuração
git commit -m "chore: atualizar dependências do projeto"
```

## 🔒 Configuração de Segurança

### Proteger branch main

1. Vá para **Settings** > **Branches** no GitHub
2. Clique em **Add rule**
3. Configure:
   - Branch name pattern: `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### Configurar secrets para CI/CD

1. Vá para **Settings** > **Secrets and variables** > **Actions**
2. Adicione secrets necessários:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - Outros conforme `.env.example`

## 🚀 Configuração de CI/CD (GitHub Actions)

Crie o arquivo `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Run linting
      run: npm run lint
```

## 📊 Comandos Úteis

```bash
# Ver histórico de commits
git log --oneline

# Ver diferenças não commitadas
git diff

# Ver diferenças entre commits
git diff HEAD~1 HEAD

# Desfazer último commit (mantendo alterações)
git reset --soft HEAD~1

# Desfazer alterações não commitadas
git checkout -- arquivo.js

# Atualizar repositório local
git pull origin main

# Ver branches remotas
git branch -r

# Limpar branches locais que não existem mais no remoto
git remote prune origin
```

## 🆘 Solução de Problemas Comuns

### Erro: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/seu-usuario/plataforma_juridica_saas.git
```

### Erro: "failed to push some refs"
```bash
# Puxar alterações primeiro
git pull origin main --rebase
# Depois fazer push
git push origin main
```

### Arquivo muito grande
```bash
# Usar Git LFS para arquivos grandes
git lfs install
git lfs track "*.pdf"
git add .gitattributes
```

---

**✅ Após seguir estes passos, seu projeto estará configurado no GitHub e pronto para desenvolvimento colaborativo!**