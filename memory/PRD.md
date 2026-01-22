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
3. **Admin**: Acesso total + Gestão de Usuários + CRUD Cadastros

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

### Backend (2026-01-22) - ATUALIZADO
- Domain Layer completo (Entidades, Value Objects, Exceções)
- **Repositórios SQLAlchemy async (compatível PostgreSQL e SQLite)**
- Use Cases: CriarPedido, AtualizarStatus, GerarExportacao, ConsultarPedidos
- JWT Authentication com roles
- Exportador XLSX para TOTVS (openpyxl)
- API RESTful com tratamento de erros
- **Dashboard 2.0 Analytics** (`GET /api/pedidos/analytics`)
- **CRUD de Cadastros** (Cursos, Projetos, Empresas)
- **Formatação automática de nomes** (Title Case com preposições)
- **Validação de CPF duplicado** no sistema
- **Importação em Lote** via planilhas Excel/CSV
- **Número de Protocolo Sequencial** (CM-YYYY-NNNN)
- **8 Novos Campos TOTVS** no modelo de Aluno
- **Central de Pendências Documentais** - NOVO! (2026-01-22)
  - CRUD completo de pendências
  - 8 tipos de documentos padronizados
  - Histórico de contatos com alunos
  - Dashboard de status

### Frontend (2026-01-22) - ATUALIZADO
- Tela de Login com identidade SENAI CIMATEC
- Dashboard Consultor (Funil de Vendas)
- Dashboard Assistente (Painel de Gestão)
- **Dashboard Admin 2.0** (KPIs, Funil, Top Empresas/Projetos, Evolução Mensal)
- **Formulário Wizard Nova Solicitação** (3 etapas) - com 8 novos campos TOTVS
- Página de Detalhes do Pedido (exibe todos os campos do aluno)
- Gestão de Usuários (CRUD)
- **Gestão de Cadastros** (Cursos, Projetos, Empresas)
- **Importação em Lote** - Wizard 4 passos
- **Coluna "Protocolo"** na listagem de pedidos
- **Exibição do Protocolo** na página de detalhes
- **Nomenclatura ajustada**: "Nova Solicitação" ao invés de "Nova Matrícula"
- **Card Resumo**: "Total de Alunos em Solicitações"
- **Central de Pendências Documentais** - NOVO! (2026-01-22)
  - Dashboard com cards de status
  - Filtros por nome, status e documento
  - Lista de pendências com dados completos
  - Modal de detalhes com histórico
  - Registro de contatos com alunos
  - Alteração de status com fluxo detalhado
- Toasts de feedback
- Rotas protegidas por role

### Dados Auxiliares (Seed)
- Cursos: 10 cursos técnicos e de engenharia
- Projetos: 4 projetos SENAI
- Empresas: 5 empresas parceiras

## Prioritized Backlog

### P0 (Concluído ✅)
- [x] Autenticação e autorização
- [x] CRUD de pedidos
- [x] Dashboard por role
- [x] Exportação TOTVS
- [x] Suporte a PostgreSQL/SQLite
- [x] Dashboard 2.0 com Analytics
- [x] CRUD de Cadastros (Cursos, Projetos, Empresas)
- [x] Importação em Lote via planilhas
- [x] Número de Protocolo Sequencial (CM-2026-0001)
- [x] 8 Novos Campos TOTVS (compatibilidade 100%)
- [x] Ajuste de Nomenclaturas (Solicitação vs Matrícula)
- [x] Central de Pendências Documentais - NOVO!

### P1 (Próximos)
- [ ] Módulo de Reembolsos (integração SGC Plus) - PRIORIDADE
- [ ] Timeline de Auditoria Visual
- [ ] Refatoração do server.py (monolito > roteadores separados)
- [ ] Refinar máquina de estados dos pedidos
- [ ] Filtros avançados de data na listagem

### P2 (Futuro)
- [ ] Notificações automáticas por email
- [ ] Controle Orçamentário para projetos
- [ ] Smart Sidebar contextual no formulário
- [ ] Integração com API de CEP (ViaCEP)
- [ ] Upload de documentos do aluno
- [ ] Expansão para outros tipos de matrículas (cursos pagos, bolsistas)

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy (Async), PostgreSQL/SQLite, Pydantic, openpyxl, pandas
- Frontend: React 19, Tailwind CSS, Shadcn/UI, React Router, Axios, Recharts
- Auth: JWT (python-jose), bcrypt (passlib)

## Database Configuration
O sistema suporta dois bancos de dados:

### PostgreSQL (Produção)
```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/db_central_matriculas
```

### SQLite (Desenvolvimento Local)
```env
# Comentar ou remover DATABASE_URL para usar SQLite
# DATABASE_URL=sqlite+aiosqlite:///./matriculas.db
```
Sem a variável DATABASE_URL, o sistema usa SQLite automaticamente em `./data/database.db`

## Default Credentials
- Admin: admin@senai.br / admin123
- Assistente: assistente@senai.br / assistente123
- Consultor: consultor@senai.br / consultor123

## Key Files
- `/app/backend/server.py` - Arquivo principal do FastAPI (monolítico, necessita refatoração)
- `/app/backend/src/utils/text_formatters.py` - Formatação de nomes (Title Case)
- `/app/frontend/src/pages/ImportacaoLotePage.jsx` - Importação em Lote
- `/app/frontend/src/pages/AdminDashboard.jsx` - Dashboard 2.0
- `/app/frontend/src/pages/GestaoUsuariosPage.jsx` - Gestão de Usuários
- `/app/frontend/src/components/DashboardLayout.jsx` - Layout principal

## API Endpoints - Importação em Lote (NOVO)
- `GET /api/importacao/template` - Download do template Excel
- `POST /api/importacao/validar` - Validação de planilha
- `POST /api/importacao/executar` - Execução da importação

## Test Reports
- `/app/test_reports/iteration_3.json` - Relatório de testes (7/7 PASS) - 2026-01-22
- `/app/test_reports/iteration_2.json` - Relatório de testes (26/26 PASS)
- `/app/tests/test_importacao_api.py` - Suite de testes da Importação em Lote

## Last Updated
2026-01-22 - Implementados 8 novos campos TOTVS + Ajuste de nomenclaturas

## 8 Novos Campos TOTVS (2026-01-22)
Campos adicionados ao modelo de Aluno para compatibilidade 100% com TOTVS:
1. `rg_data_emissao` - Data de emissão do RG
2. `naturalidade` - Cidade de nascimento
3. `naturalidade_uf` - Estado de nascimento
4. `sexo` - M/F
5. `cor_raca` - Conforme IBGE
6. `grau_instrucao` - Nível de escolaridade
7. `nome_pai` - Nome completo do pai
8. `nome_mae` - Nome completo da mãe
