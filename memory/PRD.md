# Sistema SYNAPSE - Hub de Inteligência Operacional SENAI CIMATEC

## Problem Statement
Sistema web completo chamado SYNAPSE para o SENAI CIMATEC - um "Hub de Inteligência Operacional" que atua como middleware de front-end entre a CAC (Central de Atendimento ao Cliente) e o TOTVS Educacional. O objetivo é substituir processos manuais para gerenciar solicitações de matrícula, pendências de documentos, reembolsos, e apoio cognitivo para funcionários.

## Última Atualização: 2026-03-09

### Auditoria de Produção (2026-03-09) - CONCLUÍDA ✅
**Todos os testes passaram:**
- Login de usuários oficiais funcionando
- Fluxo de primeiro acesso com troca de senha obrigatória validado
- Assistente TOTVS carregando dados corretamente
- Formatador de Planilhas interface funcionando
- Menu lateral corrigido (Exportar TOTVS no rodapé)
- Botão "Assistente TOTVS" adicionado na página de detalhes do pedido
- Botão "Preencher TOTVS para [Nome]" por aluno implementado

### Botão Assistente TOTVS na Página de Detalhes (2026-03-09) - NOVO! ✅
**Nova integração do Assistente TOTVS:**
- Botão "Assistente TOTVS" no header da página de detalhes
- Botão individual "Preencher TOTVS para [Nome]" em cada card de aluno
- Navegação direta com dados pré-carregados
- Disponível para perfis: Assistente, Admin

### Fluxo de Cancelamento de Matrícula (2026-02-27) ✅
- Nova página `/cancelamentos` no menu lateral
- Cards de responsabilidades por status (CAC, CAA)
- Busca de pedido por ID ou protocolo
- Modal de solicitação de cancelamento com 4 tipos
- Indicador de prazo NRM com barra de progresso
- Endpoints: `/api/cancelamento/solicitar`, `/api/cancelamento/resposta-nrm`

### Templates de Mensagem Integrados (2026-02-27) ✅
- Aba WhatsApp com 9 templates prontos
- Aba Email com 8 templates HTML
- Substituição automática de variáveis
- Botão "Copiar" e "Abrir WhatsApp/Email"

### Formatador de Planilhas (2026-02-27) ✅
- Página `/formatador` no menu lateral
- Upload de arquivos .xls e .xlsx
- Formatação automática de nomes, CPFs, telefones, emails, CEPs, datas
- Detecta CPFs inválidos automaticamente
- Regras do programa Brasil Mais Produtivo (BMP)

## Architecture
### Backend (Clean Architecture)
- **Domain Layer**: Entidades ricas, Value Objects, Interfaces de Repositório
- **Application Layer**: Use Cases, DTOs
- **Infrastructure Layer**: Repositórios SQLAlchemy (PostgreSQL/SQLite), JWT Auth
- **Interface Layer**: Controllers FastAPI, Middlewares
- **Services Layer**: Regras de Negócio SENAI, Templates de Mensagem

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
- [x] **Auditoria de Produção** ✅ (2026-03-09)

### P1 (Próximos)
- [ ] Implementar filtros por intervalo de datas nas listagens
- [ ] Investigar problema da planilha SESI (layout incorreto)
- [ ] Dashboard de SLA por atendente

### P2 (Futuro)
- [ ] Refatorar `server.py` monolítico (dívida técnica)
- [ ] Padronizar caminho do banco de dados
- [ ] Integração com Portal do Aluno
- [ ] Upload de documentos do aluno

## Key Files
- `/app/backend/server.py` - Arquivo principal do FastAPI
- `/app/frontend/src/pages/AssistenteTOTVSPage.jsx` - Assistente TOTVS
- `/app/frontend/src/pages/PedidoDetalhePage.jsx` - Detalhes do pedido (com botões TOTVS)
- `/app/frontend/src/pages/TrocarSenhaPrimeiroAcessoPage.jsx` - Primeiro acesso
- `/app/frontend/src/components/DashboardLayout.jsx` - Layout com menu lateral

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Axios, Recharts
- Auth: JWT (python-jose), bcrypt (passlib)

## Last Updated
2026-03-09 - Auditoria de produção concluída, botões Assistente TOTVS adicionados na página de detalhes
