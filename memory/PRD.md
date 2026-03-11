# Sistema SYNAPSE - Hub de Inteligência Operacional SENAI CIMATEC

## Problem Statement
Sistema web completo chamado SYNAPSE para o SENAI CIMATEC - um "Hub de Inteligência Operacional" que atua como middleware de front-end entre a CAC (Central de Atendimento ao Cliente) e o TOTVS Educacional. O objetivo é substituir processos manuais para gerenciar solicitações de matrícula, pendências de documentos, reembolsos, e apoio cognitivo para funcionários.

## Última Atualização: 2026-03-11

### Manual do Sistema (2026-03-11) - CONCLUÍDO
- Página `/manual` com busca, tabs (Módulos, Perfis, FAQ)
- 10 módulos documentados com funcionalidades e dicas
- 3 perfis com permissões detalhadas
- 6 perguntas frequentes
- Seção de contato/suporte
- Acessível para todos os perfis

### Dashboard de Produtividade (2026-03-11) - CONCLUÍDO
- Página `/produtividade` para coordenadora acompanhar equipe
- 6 KPIs: Pedidos, Aprovados, Reembolsos, Auditorias, Média/Dia, Membros Ativos
- Gráfico de ranking de atividade por membro (barras empilhadas)
- Gráfico de evolução diária (linhas)
- Tabela detalhada por membro com todas as métricas
- Filtro por período (7d, 15d, 30d, 90d, todo período)
- Backend: `/api/produtividade/dashboard` com aggregações em tempo real
- Restrito a admin e assistente

### Filtro por Período Letivo no Painel de Vagas (2026-03-11) - CONCLUÍDO
- Seletor de período letivo no topo da página (dropdown)
- Dashboard e lista de turmas filtrados pelo período selecionado
- Período mais recente selecionado como padrão (ex: 2026.1)
- Novo endpoint `/api/painel-vagas/periodos` para listar períodos disponíveis
- Coluna "Período" adicionada à tabela de turmas
- Badge visual no subtítulo mostrando período ativo

### Limpeza de Nomes de Cursos (2026-03-11) - CONCLUÍDO
- 3 cursos limpos: removidos prefixos numéricos indevidos
- "3003Técnico em Design de Interiores" -> "Técnico em Design de Interiores"
- "821Técnico em Gráfica Offset Plana e Rotativa" -> removido (duplicata)
- "9270 Auxiliar de Obras de Edificações" -> removido (duplicata)
- 6 cursos mantidos (prefixos válidos: 1ª, 2ª, 2D, etc.)

### Refatoração do Backend (2026-03-10) - CONCLUÍDA
- server.py reduzido de 1685 para ~350 linhas (80% de redução)
- Rotas movidas para roteadores modulares em src/routers/
- Banco consolidado em /app/data/database.db

### Correção de Dados (2026-03-10) - CONCLUÍDA
- Corrigido número de turmas, vagas, ocupação
- Removida duplicata de cursos
- Dashboards auditados e consistentes

## Architecture
### Backend (Clean Architecture - Refatorado)
- Domain Layer: Entidades, Value Objects, Interfaces
- Application Layer: Use Cases, DTOs
- Infrastructure Layer: SQLAlchemy (SQLite), JWT Auth
- Interface Layer: Controllers FastAPI modulares
- Services Layer: Regras de Negócio SENAI

### Estrutura de Routers
```
/app/backend/src/routers/
├── auth_routes.py      # Login, registro, primeiro acesso
├── pedidos_routes.py   # CRUD pedidos, dashboard, analytics
├── usuarios_routes.py  # CRUD usuários (admin)
├── auxiliares.py       # Status e dados auxiliares
├── reembolsos.py       # Módulo de reembolsos
├── pendencias.py       # Central de pendências
├── turmas.py           # Gestão de turmas
├── chamados_sgc.py     # Chamados SGC Plus
├── painel_vagas.py     # Dashboard de vagas
├── cadastros.py        # CRUD cursos, projetos, empresas
├── apoio_cognitivo.py  # Meu Dia, base de conhecimento
├── sla_dashboard.py    # Dashboard SLA
├── produtividade.py    # Dashboard de Produtividade (NOVO)
├── alertas.py          # Central de Alertas
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

## Credenciais de Acesso
- Admin: `pedro.passos@fieb.org.br` (senha alterada: Pedro@2026)
- Admin: `cristiane.mendes@fieb.org.br` (senha: NovaSenha123)
- Assistentes: camila, vanessa, saulo, vitoria, jose.hericles
- Consultor: consultorexemplocimatec@fieb.org.br
- Senha padrão: Senai@2026

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
- [x] **Manual do Sistema** (2026-03-11)
- [x] **Dashboard de Produtividade** (2026-03-11)
- [x] **Limpeza de Nomes de Cursos** (2026-03-11)

### P1 (Próximos)
- [ ] Filtros por intervalo de datas nas listagens
- [ ] Dashboard SLA por atendente
- [ ] Limpeza do requirements.txt

### P2 (Futuro)
- [ ] Investigar planilha SESI (bloqueado - aguarda arquivo)
- [ ] Integração com TOTVS via API (aguardando TI)
- [ ] Evoluir Arquitetura da Informação (nomes de menus)
- [ ] Upload de documentos do aluno
- [ ] Integração com Portal do Aluno

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Axios, Recharts
- Auth: JWT (python-jose), bcrypt

## Dados Atuais
- 413 pedidos de matrícula
- 50 reembolsos
- 10 turmas (420 vagas, 376 ocupadas)
- 4487 cursos catalogados e categorizados
- 11 usuários cadastrados

## Key Files
- `/app/backend/server.py` - FastAPI principal (~350 linhas)
- `/app/backend/src/routers/produtividade.py` - Router de produtividade (NOVO)
- `/app/frontend/src/pages/ProdutividadePage.jsx` - Dashboard Produtividade (NOVO)
- `/app/frontend/src/pages/ManualAjudaPage.jsx` - Manual do Sistema
- `/app/frontend/src/App.js` - Rotas
- `/app/frontend/src/components/DashboardLayout.jsx` - Sidebar
