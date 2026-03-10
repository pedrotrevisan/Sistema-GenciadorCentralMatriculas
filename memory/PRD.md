# Sistema SYNAPSE - Hub de Inteligência Operacional SENAI CIMATEC

## Problem Statement
Sistema web completo chamado SYNAPSE para o SENAI CIMATEC - um "Hub de Inteligência Operacional" que atua como middleware de front-end entre a CAC (Central de Atendimento ao Cliente) e o TOTVS Educacional. O objetivo é substituir processos manuais para gerenciar solicitações de matrícula, pendências de documentos, reembolsos, e apoio cognitivo para funcionários.

## Última Atualização: 2026-03-10

### Refatoração do Backend (2026-03-10) - CONCLUÍDA ✅
**Melhorias técnicas implementadas:**
- **server.py:** Reduzido de 1685 linhas para 339 linhas (80% de redução!)
- **Arquitetura modular:** Rotas movidas para arquivos específicos:
  - `auth_routes.py` - Autenticação, login, registro, primeiro acesso
  - `pedidos_routes.py` - CRUD de pedidos, dashboard, analytics, timeline
  - `usuarios_routes.py` - CRUD de usuários (admin)
  - `auxiliares.py` - Status de pedido e dados auxiliares
- **Banco de dados:** Consolidado em `/app/data/database.db` (removido arquivo duplicado)
- **Limpeza:** Removidos arquivos de backup e duplicatas

### Correção de Dados (2026-03-10) - CONCLUÍDA ✅
**Sincronização com planilha original CHP 2026.1:**
- Corrigido número de turmas: 11 → **10 turmas**
- Corrigido total de vagas: 438 → **420 vagas**
- Corrigido ocupação: 410 → **376 alunos** (89.5%)
- Corrigido vagas disponíveis: 28 → **44 vagas**
- Removida duplicata "Petroquímica/Petroquimíca"
- Sincronizado painel de vagas com dados reais dos pedidos
- Atualizado modo apresentação e propostas com números corretos

### Cards de KPI Clicáveis (2026-03-09) - CONCLUÍDO ✅
**Implementada funcionalidade de cards clicáveis em todas as páginas de dashboard:**
- **Reembolsos:** Cards de Abertos, Aguardando, No Financeiro, Pagos e Total Geral agora filtram a lista ao clicar
- **Pendências Documentais:** Cards de Pendentes, Aguardando Aluno, Em Análise, Reenvio, Aprovados e Críticas filtram ao clicar
- **Pedidos (Painel de Gestão):** Cards de Total, Pendentes, Em Análise, Doc. Pend., Aprovados, Realizados, Exportados e Rejeitados filtram ao clicar
- **Chamados SGC:** Cards de Em Aberto, Críticos, SLA Crítico e Fechados Hoje filtram ao clicar
- **Dashboard SLA:** Cards já eram clicáveis e navegam para as páginas correspondentes
- Efeito visual de hover com scale e shadow para indicar interatividade

### Painel de Vagas (2026-03-09) - CONCLUÍDO ✅
**Novo módulo para controle visual de ocupação de vagas por curso/turma:**
- Dashboard com 6 KPIs: Turmas, Total Vagas, Ocupadas, Disponíveis, Ocupação Geral, Lotando
- **Barras de ocupação visuais** por curso (ordenadas por % de ocupação)
- Resumo por turno (Matutino/Noturno) com ícones
- Alertas de turmas lotando (>= 85%)
- Lista de turmas com filtros por turno e busca
- Cadastro de novas turmas
- **10 cursos do CIMATEC 2026.1** (420 vagas totais, 376 ocupadas)

### Módulo Chamados SGC Plus (2026-03-09) - CONCLUÍDO ✅
**Novo módulo para gestão de demandas de matrícula BMP recebidas via SGC Plus:**
- Página `/chamados-sgc` no menu lateral
- Dashboard com KPIs (Em Aberto, Críticos, SLA Crítico, Fechados Hoje)
- Formulário completo baseado no questionário SGC Plus com 6 seções
- CRUD completo de chamados
- Gestão de status e sistema de interações

## Architecture
### Backend (Clean Architecture - Refatorado)
- **Domain Layer**: Entidades ricas, Value Objects, Interfaces de Repositório
- **Application Layer**: Use Cases, DTOs
- **Infrastructure Layer**: Repositórios SQLAlchemy (SQLite), JWT Auth
- **Interface Layer**: Controllers FastAPI modulares
- **Services Layer**: Regras de Negócio SENAI, Templates de Mensagem

### Estrutura de Routers Refatorada
```
/app/backend/src/routers/
├── auth_routes.py      # Login, registro, primeiro acesso, painel de conta
├── pedidos_routes.py   # CRUD pedidos, dashboard, analytics, timeline
├── usuarios_routes.py  # CRUD usuários (admin)
├── auxiliares.py       # Status de pedido e dados auxiliares
├── reembolsos.py       # Módulo de reembolsos
├── pendencias.py       # Central de pendências
├── turmas.py           # Gestão de turmas
├── chamados_sgc.py     # Chamados SGC Plus
├── painel_vagas.py     # Dashboard de vagas
├── cadastros.py        # CRUD cursos, projetos, empresas
├── apoio_cognitivo.py  # Meu Dia, base de conhecimento
└── ... (outros módulos)
```

### Frontend (React)
- React 19 + Tailwind CSS + Shadcn/UI
- Roteamento protegido por RBAC
- Identidade visual SENAI CIMATEC (#004587 azul, #E30613 vermelho)

## User Personas
1. **Consultor**: Cria e visualiza próprios pedidos de matrícula
2. **Assistente**: Visualiza todos os pedidos, altera status, exporta TOTVS
3. **Admin**: Acesso total + Gestão de Usuários + CRUD Cadastros

## Credenciais de Acesso (Produção)
**Administradores:**
- `pedro.passos@fieb.org.br` (já alterou senha)
- `cristiane.mendes@fieb.org.br` (senha: NovaSenha123)

**Assistentes:**
- `camila.mreis@fieb.org.br`
- `vanessa.silvasantos@fieb.org.br`
- `saulo.serra@fbest.org.br`
- `vitoria.soliveira@fbest.org.br` (senha: NovaSenha123)
- `jose.hericles@fieb.org.br`

**Consultor:**
- `consultorexemplocimatec@fieb.org.br`

**Senha Padrão para primeiro acesso:** `Senai@2026`

## Prioritized Backlog

### P0 (Concluído ✅)
- [x] Autenticação oficial com troca de senha obrigatória
- [x] CRUD de pedidos
- [x] Dashboard por role
- [x] Exportação TOTVS
- [x] Central de Pendências Documentais
- [x] Módulo de Reembolsos
- [x] Dashboard BI com gráficos
- [x] Kanban Board
- [x] Apoio Cognitivo ("Meu Dia", Base de Conhecimento)
- [x] Assistente TOTVS
- [x] Formatador de Planilhas (BMP)
- [x] Fluxo de Cancelamento
- [x] Módulo Chamados SGC Plus
- [x] Painel de Vagas
- [x] Auditoria de Produção
- [x] **Refatoração do server.py** ✅ (2026-03-10)
- [x] **Consolidação do banco de dados** ✅ (2026-03-10)

### P1 (Próximos)
- [ ] Implementar filtros por intervalo de datas nas listagens
- [ ] Investigar problema da planilha SESI (layout incorreto)
- [ ] Dashboard de SLA por atendente
- [ ] Dashboard de Produtividade da equipe (para Cristiane)

### P2 (Futuro)
- [ ] Integração com Portal do Aluno
- [ ] Upload de documentos do aluno
- [ ] Integração com TOTVS via API (aguardando aprovação da TI)

## Key Files
- `/app/backend/server.py` - Arquivo principal do FastAPI (refatorado - 339 linhas)
- `/app/backend/src/routers/auth_routes.py` - Router de autenticação (novo)
- `/app/backend/src/routers/pedidos_routes.py` - Router de pedidos (novo)
- `/app/backend/src/routers/usuarios_routes.py` - Router de usuários (novo)
- `/app/backend/src/routers/chamados_sgc.py` - Router para Chamados SGC Plus
- `/app/backend/src/routers/painel_vagas.py` - Router para Painel de Vagas
- `/app/frontend/src/pages/ChamadosSGCPage.jsx` - Página do módulo Chamados SGC
- `/app/frontend/src/pages/PainelVagasPage.jsx` - Página do Painel de Vagas
- `/app/frontend/src/pages/ApresentacaoPage.jsx` - Modo de apresentação
- `/app/frontend/src/pages/PropostaCristianePage.jsx` - Proposta para coordenação
- `/app/frontend/src/pages/PropostaNDSIPage.jsx` - Proposta técnica para TI

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Axios, Recharts
- Auth: JWT (python-jose), bcrypt (passlib)

## Dados Atuais
- **413 pedidos de matrícula** (293 PAGANTE, 85 BOLSISTA, 34 CAI)
- **50 reembolsos** (20 abertos, 25 pagos, 5 outros)
- **10 turmas** com 420 vagas (376 ocupadas, 44 disponíveis)
- **3 chamados SGC** de teste
- **11 usuários** cadastrados

## Last Updated
2026-03-10 - Refatoração técnica do backend concluída. Sistema 80% mais enxuto e modular.
