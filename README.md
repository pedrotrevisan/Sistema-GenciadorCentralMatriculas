# 🚀 SYNAPSE - Sistema Central de Matrículas

## Sistema Web Portátil e Inteligente para Gestão de Matrículas SENAI CIMATEC

[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)](https://sqlite.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://react.dev)
[![OCR](https://img.shields.io/badge/OCR-EasyOCR-FF6B6B?logo=python)](https://github.com/JaidedAI/EasyOCR)

---

## ✨ Novidades - Sistema Ultra Portátil!

### 🎯 **Zero Configuração**
- ✅ **Banco SQLite** (arquivo único - sem instalação de banco!)
- ✅ **OCR Offline** com EasyOCR (extração de CNH/RG sem API externa)
- ✅ **Scripts automáticos** de setup para Windows, Linux e Mac
- ✅ **Plug & Play** - copie a pasta e execute!

### 🚀 **Instalação Rápida**

```bash
# Windows
setup.bat  # Instala tudo automaticamente
start.bat  # Inicia o sistema

# Linux/Mac
./setup.sh   # Instala tudo automaticamente
./start.sh   # Inicia o sistema
```

**Pronto! Acesse:** http://localhost:3000

---

## 🏗️ Arquitetura

- **Backend:** FastAPI + SQLAlchemy (Async) + SQLite/PostgreSQL
- **Frontend:** React + Vite + Tailwind CSS + Shadcn/UI
- **Autenticação:** JWT com RBAC (Admin, Assistente, Consultor)
- **OCR:** EasyOCR (offline) + Tesseract (fallback) + Google Vision (opcional)

---

## 📋 Pré-requisitos Mínimos

- **Python 3.8+** → [Download](https://python.org)
- **Node.js 16+** → [Download](https://nodejs.org)

**Opcional** (para melhor OCR):
- Tesseract OCR → [Instruções de instalação](/README_INSTALL.md#opcional-para-melhor-desempenho-ocr)

---

## ⚡ Guia Rápido de Instalação

### Opção 1: Setup Automático (Recomendado)

**Windows:**
```batch
setup.bat   # Instala todas as dependências
start.bat   # Inicia backend + frontend
```

**Linux/Mac:**
```bash
chmod +x setup.sh start.sh
./setup.sh   # Instala todas as dependências
./start.sh   # Inicia backend + frontend
```

### Opção 2: Instalação Manual

#### Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

#### Frontend (Terminal 2)

```bash
cd frontend
yarn install  # ou npm install
yarn dev      # ou npm run dev
```

**Banco de dados:** SQLite é usado automaticamente (arquivo `/data/database.db`)

---

## 🌐 URLs do Sistema

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentação Interativa:** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

---

## 🔐 Credenciais Padrão

| Perfil | Email | Senha |
|--------|-------|-------|
| **Admin** | admin@senai.br | admin123 |
| **Assistente** | assistente@senai.br | assistente123 |
| **Consultor** | consultor@senai.br | consultor123 |

---

## 🎯 Funcionalidades Principais

### 📝 Gestão de Solicitações
- ✅ CRUD completo de pedidos de matrícula
- ✅ Suporte a 20+ campos compatíveis com TOTVS
- ✅ Tipos de vínculo: Projeto, Empresa, Brasil Mais Produtivo
- ✅ Integração com ViaCEP (preenchimento automático de endereço)
- ✅ Timeline de auditoria visual
- ✅ Importação em lote via planilhas

### 🤖 OCR Inteligente (NOVO!)
- ✅ **Extração automática de dados** de CNH e RG
- ✅ **100% Offline** - funciona sem internet (EasyOCR)
- ✅ **Múltiplos engines:** EasyOCR (padrão), Tesseract (fallback), Google Vision (opcional)
- ✅ **Suporte a:** JPG, PNG, PDF
- ✅ **Campos extraídos:** Nome, CPF, RG, Data de Nascimento, Nome da Mãe, etc.
- ✅ **Auto-preenchimento** do formulário de matrícula

### 📋 Central de Pendências
- ✅ Gestão de documentos faltantes
- ✅ Histórico de contatos com alunos
- ✅ Status e prazos de entrega

### 💰 Módulo de Reembolsos
- ✅ Gestão completa do fluxo de reembolso
- ✅ Dados bancários e comprovantes
- ✅ Templates de email personalizados

### 📊 Dashboard Unificado
- ✅ KPIs e visão geral de todas as operações
- ✅ Gráficos interativos (Recharts)
- ✅ Filtros avançados por status, data, etc.

---

## 🔧 Configuração do Sistema

### Banco de Dados

**Padrão: SQLite** (sem configuração)
```
Arquivo: /data/database.db
Backup: Copiar o arquivo .db
```

**Opcional: PostgreSQL** (para produção)
```env
# Edite backend/.env
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
```

### OCR Engine

**Padrão: EasyOCR** (offline, gratuito)
```env
# Edite backend/.env
OCR_ENGINE="easyocr"  # Padrão
# OCR_ENGINE="tesseract"  # Mais rápido, menos preciso
# OCR_ENGINE="google_vision"  # Mais preciso, requer API key
```

**Google Cloud Vision** (melhor precisão):
```env
OCR_ENGINE="google_vision"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
GOOGLE_CLOUD_PROJECT_ID="your-project-id"
```

---

## 📦 Estrutura do Projeto

```
SYNAPSE/
├── setup.py / setup.bat / setup.sh  # Scripts de instalação
├── start.bat / start.sh             # Scripts de inicialização
├── backend/                         # API FastAPI
│   ├── server.py                    # Servidor principal
│   ├── src/
│   │   ├── domain/                  # Entidades e regras de negócio
│   │   ├── application/             # Casos de uso
│   │   ├── infrastructure/          # Banco, autenticação
│   │   ├── routers/                 # Endpoints da API
│   │   └── services/                # Serviços (OCR, etc)
│   └── tests/                       # Testes automatizados
├── frontend/                        # Interface React
│   └── src/
│       ├── pages/                   # Páginas do sistema
│       ├── components/              # Componentes reutilizáveis
│       └── services/                # Chamadas API
├── data/                            # Banco SQLite
│   └── database.db
└── README_INSTALL.md                # Guia detalhado
```

---

## 🐛 Solução de Problemas

Consulte o [Guia de Instalação Detalhado](/README_INSTALL.md) para:
- Problemas comuns e soluções
- Configuração avançada
- Deploy em produção
- Backup e restauração

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
