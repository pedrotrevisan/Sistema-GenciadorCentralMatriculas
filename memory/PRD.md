# Sistema Central de Matrículas (CM) - SENAI CIMATEC

## Problem Statement
Construir um sistema web completo para gerenciamento de matrículas do SENAI CIMATEC, com backend em Python (FastAPI) utilizando Clean Architecture e Domain-Driven Design (DDD), e frontend moderno em React com identidade visual institucional.

## Architecture
### Backend (Clean Architecture)
- **Domain Layer**: Entidades ricas (PedidoMatricula, Aluno, Usuario), Value Objects (CPF, Email, Telefone, StatusPedido), Interfaces de Repositório
- **Application Layer**: Use Cases (CriarPedido, AtualizarStatus, GerarExportacao, ConsultarPedidos), DTOs
- **Infrastructure Layer**: Repositórios SQLAlchemy (PostgreSQL/SQLite), Exportador XLSX/CSV, JWT Authentication
- **Interface Layer**: Controllers FastAPI, Middlewares

### Frontend (React)
- React 19 + Tailwind CSS + Shadcn/UI
- Roteamento protegido por RBAC
- Identidade visual SENAI CIMATEC (#004587 azul, #E30613 vermelho)

## User Personas
1. **Consultor**: Cria e visualiza próprios pedidos de matrícula
2. **Assistente**: Visualiza todos os pedidos, altera status, exporta TOTVS
3. **Admin**: Acesso total + Gestão de Usuários

## Core Requirements (Static)
- [x] Autenticação JWT com RBAC
- [x] CRUD de Pedidos de Matrícula
- [x] Wizard multi-etapas para criação de pedidos
- [x] Validação de CPF brasileiro
- [x] Exportação para TOTVS (XLSX)
- [x] Dashboard com métricas por status
- [x] Gestão de Usuários (Admin)
- [x] Clean Architecture + DDD
- [x] Suporte a PostgreSQL e SQLite

## What's Been Implemented

### Backend (2026-01-10)
- Domain Layer completo (Entidades, Value Objects, Exceções)
- **Repositórios SQLAlchemy async (compatível PostgreSQL e SQLite)**
- Use Cases: CriarPedido, AtualizarStatus, GerarExportacao, ConsultarPedidos
- JWT Authentication com roles
- Exportador XLSX para TOTVS (openpyxl)
- API RESTful com tratamento de erros
- **Migração completa de MongoDB para SQLAlchemy**

### Frontend
- Tela de Login com identidade SENAI CIMATEC
- Dashboard Consultor (Funil de Vendas)
- Dashboard Assistente (Painel de Gestão)
- Dashboard Admin (Visão Geral + Ações Rápidas)
- Formulário Wizard Nova Matrícula (3 etapas)
- Página de Detalhes do Pedido
- Gestão de Usuários (CRUD)
- Toasts de feedback
- Rotas protegidas por role

### Dados Auxiliares (Mock)
- Cursos: 8 cursos técnicos e de engenharia
- Projetos: 4 projetos SENAI
- Empresas: 5 empresas parceiras

## Prioritized Backlog

### P0 (Concluído ✅)
- [x] Autenticação e autorização
- [x] CRUD de pedidos
- [x] Dashboard por role
- [x] Exportação TOTVS
- [x] Suporte a PostgreSQL/SQLite

### P1 (Próximos)
- [ ] Filtros avançados de data na listagem
- [ ] Histórico de auditoria na UI
- [ ] Notificações por email
- [ ] Upload de documentos do aluno

### P2 (Futuro)
- [ ] Dashboard com gráficos (Recharts)
- [ ] Relatórios em PDF
- [ ] Integração real com TOTVS
- [ ] API de CEP (ViaCEP)

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy (Async), PostgreSQL/SQLite, Pydantic, openpyxl
- Frontend: React 19, Tailwind CSS, Shadcn/UI, React Router, Axios
- Auth: JWT (python-jose), bcrypt (passlib)

## Database Configuration
O sistema suporta dois bancos de dados:

### PostgreSQL (Produção/Local)
```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/db_central_matriculas
```

### SQLite (Desenvolvimento)
Sem a variável DATABASE_URL, o sistema usa SQLite automaticamente em `./data/database.db`

## Default Credentials
- Admin: admin@senai.br / admin123
- Assistente: assistente@senai.br / assistente123
- Consultor: consultor@senai.br / consultor123

## Files Changed (2026-01-10)
- `/app/backend/src/infrastructure/persistence/database.py` - Suporte PostgreSQL/SQLite
- `/app/backend/src/infrastructure/persistence/repositories/*.py` - Repositórios SQLAlchemy
- `/app/backend/.env` - Configuração do ambiente
- `/app/backend/requirements.txt` - Dependências atualizadas
- `/app/README.md` - Instruções de instalação atualizadas
