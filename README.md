# Sistema Central de Matrículas - SENAI CIMATEC

Sistema web para gerenciamento de matrículas com Clean Architecture, RBAC e suporte a PostgreSQL.

## Arquitetura

- **Backend:** FastAPI + SQLAlchemy (Async) + PostgreSQL/SQLite
- **Frontend:** React + Tailwind CSS + Shadcn/UI
- **Autenticação:** JWT com RBAC (Admin, Assistente, Consultor)

---

## Instalação Local

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (recomendado) ou SQLite (desenvolvimento)

---

## Opção 1: Com PostgreSQL (Recomendado)

### 1. Configurar PostgreSQL

```sql
-- Criar banco de dados
CREATE DATABASE db_central_matriculas;

-- Criar usuário (opcional)
CREATE USER phtpa_user WITH PASSWORD '682889';
GRANT ALL PRIVILEGES ON DATABASE db_central_matriculas TO phtpa_user;
```

### 2. Backend (Terminal 1)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Crie o arquivo `.env`:
```env
DATABASE_URL=postgresql+asyncpg://phtpa_user:682889@localhost:5432/db_central_matriculas
JWT_SECRET_KEY=sua-chave-secreta-aqui
CORS_ORIGINS=http://localhost:3000
```

Inicie o servidor:
```powershell
uvicorn server:app --reload --port 8001
```

### 3. Frontend (Terminal 2)

```powershell
cd frontend
npm install
```

Crie o arquivo `.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

Inicie o frontend:
```powershell
npm start
```

---

## Opção 2: Com SQLite (Desenvolvimento Rápido)

### Backend (Terminal 1)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
mkdir data
```

Crie o arquivo `.env` **sem** DATABASE_URL para usar SQLite:
```env
JWT_SECRET_KEY=sua-chave-secreta-aqui
CORS_ORIGINS=http://localhost:3000
```

Inicie o servidor:
```powershell
uvicorn server:app --reload --port 8001
```

### Frontend (Terminal 2)

```powershell
cd frontend
npm install
```

Crie o arquivo `.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

Inicie o frontend:
```powershell
npm start
```

---

## Acessar

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8001/docs

### Credenciais Padrão

| Perfil | Email | Senha |
|--------|-------|-------|
| Admin | admin@senai.br | admin123 |
| Assistente | assistente@senai.br | assistente123 |
| Consultor | consultor@senai.br | consultor123 |

---

## Funcionalidades por Perfil

### Consultor
- Criar pedidos de matrícula
- Visualizar e editar seus próprios pedidos

### Assistente
- Todas as permissões do Consultor
- Visualizar todos os pedidos
- Atualizar status dos pedidos

### Admin
- Todas as permissões do Assistente
- Gerenciar usuários
- Exportar dados para TOTVS (XLSX)

---

## Estrutura do Projeto

```
├── backend/
│   ├── server.py              # Aplicação FastAPI
│   ├── requirements.txt       # Dependências Python
│   ├── .env                   # Configurações (criar)
│   └── src/
│       ├── domain/            # Entidades e regras de negócio
│       ├── application/       # Casos de uso e DTOs
│       ├── infrastructure/    # Repositórios e persistência
│       └── interface/         # Controllers e schemas
└── frontend/
    ├── src/
    │   ├── pages/             # Páginas da aplicação
    │   ├── components/        # Componentes React
    │   └── contexts/          # Contextos (Auth)
    └── package.json
```

---

## Troubleshooting

### Erro: "Connection refused" no PostgreSQL
- Verifique se o PostgreSQL está rodando
- Confirme usuário, senha e nome do banco no `.env`
- Para WSL2: use `localhost` ou o IP do host Windows

### Erro: "ModuleNotFoundError"
```powershell
pip install -r requirements.txt
```

### Banco não inicializa
O sistema cria as tabelas automaticamente na primeira execução.
Para PostgreSQL, apenas o banco precisa existir previamente.
