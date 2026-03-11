# Sistema SYNAPSE - Hub de Inteligência Operacional SENAI CIMATEC

## Problem Statement
Sistema web completo chamado SYNAPSE para o SENAI CIMATEC - um "Hub de Inteligência Operacional" que atua como middleware de front-end entre a CAC (Central de Atendimento ao Cliente) e o TOTVS Educacional. O objetivo é substituir processos manuais para gerenciar solicitações de matrícula, pendências de documentos, reembolsos, e apoio cognitivo para funcionários.

## Última Atualização: 2026-03-11 (Sessão 2)

## Tech Stack Atual
- Backend: Python 3.10+, FastAPI, **MongoDB (Motor/PyMongo)**, Pydantic
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Axios, Recharts
- Auth: JWT (python-jose), bcrypt
- Deploy: Emergent Platform (Kubernetes)
- Auto-seeding: initial_data.json.gz (5426 docs, 283KB comprimido)

## Credenciais de Acesso
- Admin: `pedro.passos@fieb.org.br` (senha: Pedro@2026)
- Admin: `cristiane.mendes@fieb.org.br` (senha: Senai@2026)
- Assistentes: camila, vanessa, saulo, vitoria, jose.hericles (senha: Senai@2026)
- Consultor: consultorexemplocimatec@fieb.org.br (senha: Senai@2026)
- Senha padrão: Senai@2026

## Architecture
### Backend (FastAPI + MongoDB)
- MongoDB: motor/pymongo para persistência
- JWT Auth: python-jose + bcrypt
- Interface Layer: Controllers FastAPI modulares em src/routers/
- Services Layer: Serviços de Negócio SENAI

### Estrutura de Routers
```
/app/backend/src/routers/
├── auth_routes.py        # Login, registro, primeiro acesso
├── pedidos_routes.py     # CRUD pedidos, dashboard, analytics, exportação TOTVS
├── usuarios_routes.py    # CRUD usuários (admin)
├── auxiliares.py         # Status e dados auxiliares
├── reembolsos.py         # Módulo de reembolsos
├── pendencias.py         # Central de pendências
├── turmas.py             # Gestão de turmas
├── chamados_sgc.py       # Chamados SGC Plus
├── painel_vagas.py       # Dashboard de vagas com filtro por período
├── cadastros.py          # CRUD cursos, projetos, empresas
├── apoio_cognitivo.py    # Meu Dia, base de conhecimento, lembretes
├── sla_dashboard.py      # Dashboard SLA
├── produtividade.py      # Dashboard de Produtividade da equipe
├── alertas.py            # Central de Alertas
├── contatos.py           # Log de contatos + retornos pendentes
├── importacao_matriculas.py  # Importação em lote via Excel/CSV
└── ... (outros módulos)
```

### Frontend (React)
- React 19 + Tailwind CSS + Shadcn/UI
- Roteamento protegido por RBAC
- Identidade visual SENAI CIMATEC (#004587 azul, #E30613 vermelho)

## User Personas
1. **Consultor**: Cria e visualiza próprios pedidos
2. **Assistente**: Visualiza todos os pedidos, altera status, exporta TOTVS
3. **Admin**: Acesso total + Gestão de Usuários + CRUD Cadastros

## Dados em Produção (MongoDB)
- 414 pedidos de matrícula
- 50 reembolsos
- 10 turmas (período 2026.1)
- 4487 cursos catalogados e categorizados
- 12 usuários cadastrados

## Prioritized Backlog

### P0 (Concluído)
- [x] Autenticação, CRUD pedidos, Dashboard, Exportação TOTVS
- [x] Central de Pendências, Reembolsos, Dashboard BI, Kanban
- [x] Apoio Cognitivo, Assistente TOTVS, Formatador, Cancelamentos
- [x] Chamados SGC, Painel de Vagas, Auditoria de Produção
- [x] Refatoração do server.py
- [x] Central de Alertas, Lembretes
- [x] Gestão de Usuários (reset senha)
- [x] Categorização de Cursos
- [x] Manual do Sistema
- [x] Dashboard de Produtividade
- [x] Filtro por Período Letivo (Painel de Vagas) + Duplicação de Período
- [x] **Migração SQLite → MongoDB** (2026-03-11) - Deploy na Emergent desbloqueado
- [x] Normalização de campos boolean no MongoDB (2026-03-11)
- [x] **Correção de módulos pós-migração** (2026-03-11)
- [x] **Auto-seeding no startup** (2026-03-11) - src/seeds/initial_data.json.gz
- [x] **Endpoint de seed via API** (2026-03-11) - /api/admin/seed/{collection}
- [x] **Apresentações atualizadas** (2026-03-11) - URLs, tech stack, números, módulos

### P1 (Próximos)
- [ ] Integração com TOTVS via API (aguardando TI SENAI)
- [ ] Dashboard SLA por atendente (detalhamento)
- [ ] Filtros por intervalo de datas nas listagens principais

### P2 (Futuro)
- [ ] Investigar planilha SESI (bloqueado - aguarda arquivo)
- [ ] Evoluir Arquitetura da Informação (nomes de menus)
- [ ] Upload de documentos do aluno
- [ ] Integração com Portal do Aluno

## Key Files
- `/app/backend/server.py` - FastAPI principal (MongoDB lifespan)
- `/app/backend/src/infrastructure/persistence/mongodb.py` - Conexão MongoDB
- `/app/backend/src/routers/` - Todos os routers da API
- `/app/frontend/src/pages/` - Páginas do frontend
- `/app/frontend/src/App.js` - Rotas
- `/app/frontend/src/components/DashboardLayout.jsx` - Sidebar

## Notes para Deploy
- MongoDB local: mongodb://localhost:27017 (Emergent provê MongoDB nativo)
- DB_NAME: synapse
- Todos os campos boolean normalizados (True/False nativo BSON)
- Não há mais dependência de SQLite/SQLAlchemy no fluxo de runtime
