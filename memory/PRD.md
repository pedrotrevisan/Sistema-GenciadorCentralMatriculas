# Sistema SYNAPSE - Hub de Inteligência Operacional SENAI CIMATEC

## Problem Statement
Sistema web completo chamado SYNAPSE para o SENAI CIMATEC - um "Hub de Inteligência Operacional" que atua como middleware de front-end entre a CAC (Central de Atendimento ao Cliente) e o TOTVS Educacional. O objetivo é substituir processos manuais para gerenciar solicitações de matrícula, pendências de documentos, reembolsos, e apoio cognitivo para funcionários.

## Architecture
### Backend (Clean Architecture)
- **Domain Layer**: Entidades ricas (PedidoMatricula, Aluno, Usuario), Value Objects (CPF, Email, Telefone, StatusPedido), Interfaces de Repositório
- **Application Layer**: Use Cases (CriarPedido, AtualizarStatus, GerarExportacao, ConsultarPedidos), DTOs
- **Infrastructure Layer**: Repositórios SQLAlchemy (PostgreSQL/SQLite), Exportador XLSX/CSV, JWT Authentication
- **Interface Layer**: Controllers FastAPI, Middlewares
- **Services Layer**: Regras de Negócio SENAI, Templates de Mensagem, Validador de Pré-Requisitos

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

### Melhorias SENAI/CAC (2026-02-24) - NOVO!
1. **Máquina de Estados Completa** - Alinhada com fluxo oficial SENAI:
   - Novos status: INSCRICAO, ANALISE_DOCUMENTAL, AGUARDANDO_PAGAMENTO, MATRICULADO, NAO_ATENDE_REQUISITO, TRANCADO, TRANSFERIDO
   - Transições válidas configuradas conforme procedimento PG-SENAI.EP 003
   - Metadados: cor, ícone, descrição, is_final

2. **Cálculo Automático de Prazos**:
   - Prazo de pendência documental (5 dias)
   - Alertas visuais (expirado, crítico, urgente, normal)
   - Cálculo de SLA por status
   - Contador regressivo visual

3. **Validador de Pré-Requisitos**:
   - Validação de idade por tipo de curso (CAI BAS: 14-21 anos, etc.)
   - Validação de escolaridade mínima
   - Checklist de documentos obrigatórios por tipo
   - Validação de vínculo com empresa

4. **Templates de Mensagem**:
   - E-mail: Documentos Pendentes, Prazo Expirando, Confirmação de Matrícula, Aguardando Pagamento
   - WhatsApp: Links wa.me automáticos
   - Formatação HTML/Texto

5. **Regras de Negócio SENAI**:
   - Tipos de curso configurados (CAI_BAS, CAI_TEC, CHP, TECNICO, etc.)
   - Documentos obrigatórios por tipo
   - Prazos configuráveis

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
- **Central de Pendências Documentais** (2026-01-22)
  - CRUD completo de pendências
  - 8 tipos de documentos padronizados
  - Histórico de contatos com alunos
  - Dashboard de status
- **Módulo de Reembolsos** - NOVO! (2026-01-22)
  - CRUD completo de solicitações de reembolso
  - 6 motivos: Sem Escolaridade, Sem Vaga, Passou Bolsista, Não Tem Vaga, Desistência (reter 10%), Outros
  - Fluxo de status: Aberto → Aguardando Dados Bancários → Enviado ao Financeiro → Pago/Cancelado
  - Integração com Nº Chamado SGC Plus
  - Dashboard de acompanhamento

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
- **Central de Pendências Documentais** (2026-01-22)
  - Dashboard com cards de status
  - Filtros por nome, status e documento
  - Lista de pendências com dados completos
  - Modal de detalhes com histórico
  - Registro de contatos com alunos
  - Alteração de status com fluxo detalhado
- **Módulo de Reembolsos** - NOVO! (2026-01-22)
  - Dashboard com cards de status (Abertos, Aguardando, No Financeiro, Pagos)
  - Lista de reembolsos com filtros
  - Modal de criação de nova solicitação
  - Modal de edição (status, datas, observações)
  - Modal de detalhes completo
  - Badge "Reter 10%" para desistência
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
- [x] Central de Pendências Documentais
- [x] Módulo de Reembolsos - NOVO!

### P1 (Próximos)
- [x] Timeline de Auditoria Visual - histórico de cada pedido ✅
- [x] Refatorar pendências para router separado ✅
- [x] Dashboard de BI com gráficos (Fase 5) ✅
- [x] Log de Contatos (Fase 3) ✅
- [x] Kanban Board interativo ✅
- [x] Nova Pendência Manual (criar sem pedido) ✅
- [x] Importação de Pendências em Lote (Excel/CSV) ✅
- [x] Cadastro de Cursos melhorado (Tipo, Modalidade, Área, Carga Horária) ✅
- [x] Refatorar cadastros para router separado (cadastros.py) ✅
- [x] Apoio Cognitivo ("Meu Dia", Base de Conhecimento) ✅ (2026-02-23)
- [x] Painel de Conta do Usuário (alterar senha, perfil) ✅ (2026-02-23)
- [x] Sistema de Atribuições/Chamados (Caixa de Entrada) ✅ (2026-02-23)
- [x] Log de Atividades na página Minha Conta ✅ (2026-02-24)
- [ ] Filtros por Data nas listagens
- [ ] Refatorar pedidos para router separado
- [ ] Refinar máquina de estados dos pedidos

### P2 (Futuro)
- [x] Notificações por email (SMTP Outlook) - ESTRUTURA PRONTA ✅ (2026-02-23)
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
- `/app/test_reports/iteration_7.json` - Timeline de Auditoria (13/13 backend + 8/8 frontend PASS) - 2026-01-22 - NOVO!
- `/app/test_reports/iteration_6.json` - Melhorias Reembolsos v1.1 (27/27 PASS) - 2026-01-22
- `/app/test_reports/iteration_5.json` - Módulo de Reembolsos (39/39 PASS) - 2026-01-22
- `/app/test_reports/iteration_4.json` - Central de Pendências (24/24 PASS) - 2026-01-22
- `/app/test_reports/iteration_3.json` - Campos TOTVS + Nomenclaturas (7/7 PASS) - 2026-01-22
- `/app/test_reports/iteration_2.json` - Importação em Lote (26/26 PASS)
- `/app/tests/test_importacao_api.py` - Suite de testes da Importação
- `/app/tests/test_pendencias_api.py` - Suite de testes da Central de Pendências
- `/app/tests/test_reembolsos_api.py` - Suite de testes do Módulo de Reembolsos (atualizada com 27 testes)
- `/app/backend/tests/test_timeline_api.py` - Suite de testes da Timeline de Auditoria
- `/app/test_reports/iteration_8.json` - Fase 2: Gestão de Pendências Documentais + BI Dashboard (25/25 PASS)
- `/app/backend/tests/test_documentos_api.py` - Suite de testes do módulo de Documentos (Clean Architecture)
- `/app/test_reports/iteration_9.json` - Fase 3: Log de Contatos (32/32 PASS) - NOVO!
- `/app/backend/tests/test_contatos_api.py` - Suite de testes do módulo de Contatos - NOVO!

## Last Updated
2026-02-24 - Log de Atividades implementado no Painel de Conta do Usuário

## Central de Pendências Documentais (2026-01-22)
Nova funcionalidade para gerenciar documentos pendentes dos alunos:

### Tipos de Documentos (Códigos)
- 94: Comprovante de Residência (obrigatório)
- 96: Solicitação Desconto (opcional)
- 97: CPF/RG Responsável Legal (se menor)
- 131: RG Frente (obrigatório)
- 132: RG Verso (obrigatório)
- 136: Comprovante Escolaridade Frente (obrigatório)
- 137: Comprovante Escolaridade Verso (obrigatório)
- 205: CPF (opcional)

### Fluxo de Status
`Pendente` → `Aguardando Aluno` → `Em Análise` → `Aprovado` / `Rejeitado` / `Reenvio Necessário`

### Endpoints da Central de Pendências
- `GET /api/pendencias/tipos-documento` - Lista tipos de documento
- `GET /api/pendencias/dashboard` - Dashboard de status
- `GET /api/pendencias/buscar-aluno/{cpf}` - Busca aluno por CPF
- `GET /api/pendencias` - Lista pendências com filtros
- `POST /api/pendencias` - Cria pendência vinculada a pedido
- `POST /api/pendencias/manual` - Cria pendência manual
- `GET /api/pendencias/importacao/template` - Download template Excel (NOVO!)
- `POST /api/pendencias/importacao/validar` - Valida arquivo para importação (NOVO!)
- `POST /api/pendencias/importacao/executar` - Executa importação em lote (NOVO!)
- `GET /api/pendencias/{id}` - Detalhes da pendência
- `PUT /api/pendencias/{id}` - Atualiza status
- `POST /api/pendencias/{id}/contatos` - Registra contato
- `DELETE /api/pendencias/{id}` - Exclui pendência (admin)

## Módulo de Documentos - Clean Architecture (2026-02-23) - NOVO!
Sistema de gestão de pendências documentais com arquitetura Clean + endpoints de BI.

### Tipos de Documento (17 tipos)
- Identidade: rg_frente, rg_verso, rg_completo, cpf, certidao_nascimento, certidao_casamento
- Escolares: historico_escolar, comprovante_escolaridade, certificado_conclusao, declaracao_matricula
- Comprovantes: comprovante_residencia, comprovante_renda
- Fotos: foto_3x4, foto_documento
- Outros: laudo_medico, declaracao_responsavel, outros

### Fluxo de Status (Clean Architecture)
`Pendente` → `Enviado` → `Em Análise` → `Aprovado` / `Recusado`
                                      ↓
                                  `Expirado`

### Endpoints de CRUD (/api/documentos)
- `GET /api/documentos/tipos` - Lista 17 tipos de documento
- `GET /api/documentos/status` - Lista status com cores
- `GET /api/documentos/prioridades` - Lista prioridades
- `POST /api/documentos` - Cria pendência documental
- `POST /api/documentos/padrao/{pedido_id}` - Cria 5 pendências padrão
- `GET /api/documentos/pedido/{pedido_id}` - Lista pendências de um pedido
- `GET /api/documentos/{id}` - Detalhes da pendência
- `POST /api/documentos/{id}/enviar` - Enviar documento
- `POST /api/documentos/{id}/validar` - Aprovar/Recusar documento
- `PUT /api/documentos/{id}/observacoes` - Atualizar observações
- `GET /api/documentos/validacao/fila` - Fila de validação

### Endpoints de Estatísticas/BI (/api/documentos)
- `GET /api/documentos/stats/resumo` - KPIs de documentos
- `GET /api/documentos/stats/por-tipo` - Estatísticas por tipo de documento
- `GET /api/documentos/stats/vencendo` - Documentos próximos a expirar
- `GET /api/documentos/bi/matriculas` - KPIs de matrículas
- `GET /api/documentos/bi/evolucao` - Evolução mensal (gráfico de linha)
- `GET /api/documentos/bi/reembolsos` - KPIs de reembolsos
- `GET /api/documentos/bi/pendencias` - KPIs de pendências
- `GET /api/documentos/bi/completo` - Dashboard completo de BI

## Scripts de Migração
- `/app/migracao_totvs_campos.sql` - 8 novos campos do aluno
- `/app/migracao_simples.sql` - Versão simplificada
- `/app/migracao_pendencias.sql` - Tabelas da Central de Pendências
- `/app/migracao_reembolsos.sql` - Tabela de Reembolsos - NOVO!

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

## Módulo de Reembolsos (2026-01-22)
Sistema de gerenciamento de solicitações de reembolso.

### Motivos de Reembolso
| Motivo | Retém Taxa (10%)? |
|--------|-------------------|
| Sem Escolaridade | ❌ Não |
| Sem Vaga 2026.1 | ❌ Não |
| Passou como Bolsista | ❌ Não |
| Não Tem Vaga | ❌ Não |
| **Desistência do Aluno** | ✅ **Sim** |
| Outros | ❌ Não |

### Fluxo de Status
```
Aberto → Aguardando Dados Bancários → Enviado ao Financeiro → Pago
                    ↓
               Cancelado
```

### Endpoints do Módulo de Reembolsos
- `GET /api/reembolsos/motivos` - Lista motivos
- `GET /api/reembolsos/status` - Lista status
- `GET /api/reembolsos/dashboard` - Dashboard
- `GET /api/reembolsos/templates-email` - Templates de email (NOVO!)
- `GET /api/reembolsos` - Lista com filtros
- `POST /api/reembolsos` - Cria reembolso
- `GET /api/reembolsos/{id}` - Detalhes
- `PUT /api/reembolsos/{id}` - Atualiza
- `DELETE /api/reembolsos/{id}` - Exclui (admin)
- `POST /api/reembolsos/{id}/dados-bancarios` - Registra dados bancários (NOVO!)
- `POST /api/reembolsos/{id}/marcar-email-enviado` - Marca email enviado (NOVO!)

### Melhorias v1.1 (2026-01-22) - NOVO!
1. **Indicador de Menor de Idade**
   - Campo `aluno_menor_idade` no formulário
   - Badge "Menor" na listagem de reembolsos
   - Reembolso deve ser feito para conta do responsável

2. **Dados Bancários**
   - Endpoint dedicado para registrar dados bancários
   - Campos: titular, CPF, banco, agência, operação, conta, tipo
   - Badge "Banco OK" indica dados recebidos

3. **Templates de Email**
   - Modal com 3 templates prontos
   - Solicitação de dados bancários
   - Confirmação de recebimento
   - Confirmação de pagamento
   - Botão "Copiar" para cada template

## Dashboard de BI - Fase 5 (2026-02-23) - NOVO!
Dashboard de Business Intelligence com gráficos interativos usando Recharts.

### Acessível via
- Menu lateral: "Dashboard BI"
- URL: `/bi`
- Perfis: Assistente, Admin

### KPIs Principais (Cards)
1. **Total Matrículas** - Com badge de matrículas do mês
2. **Taxa de Conversão** - Indicador de meta (acima/abaixo)
3. **Pendências Abertas** - Link para central de pendências
4. **Reembolsos Pendentes** - Link para módulo de reembolsos
5. **Aprovação de Documentos** - Taxa percentual

### Abas do Dashboard
1. **Visão Geral**
   - Gráfico de área: Evolução de Matrículas (6 meses)
   - Gráfico de pizza: Distribuição por Status
   - Cards de resumo: Matrículas, Pendências, Reembolsos

2. **Matrículas**
   - Gráfico de barras: Funil de Conversão
   - Gráfico radial: Taxa de Conversão (meta 70%)
   - Grid: Detalhamento por Status

3. **Documentos**
   - Cards: Total, Pendentes, Em Análise, Aprovados
   - Barra de progresso: Taxa de Aprovação

4. **Financeiro**
   - Cards: Total, Abertos, No Financeiro, Pagos
   - Gráfico de barras: Fluxo de Reembolsos
   - Alerta: Reembolsos com retenção de 10%

### Tecnologias
- Frontend: React + Recharts
- Backend: Endpoints `/api/documentos/bi/*`

## Log de Contatos - Fase 3 (2026-02-23) - NOVO!
Sistema para registrar e consultar todas as interações com alunos.

### Tipos de Contato (6 tipos)
- `ligacao` - Ligação Telefônica
- `whatsapp` - WhatsApp
- `email` - E-mail
- `presencial` - Presencial
- `sms` - SMS
- `outro` - Outro

### Resultados de Contato (7 resultados)
- `sucesso` - Conseguiu falar/contactar
- `nao_atendeu` - Não atendeu ligação
- `caixa_postal` - Caiu na caixa postal
- `numero_errado` - Número incorreto
- `sem_resposta` - WhatsApp/Email sem resposta
- `pendente` - Aguardando retorno
- `agendado` - Retorno agendado

### Motivos de Contato (10 motivos)
- documentacao, acompanhamento, confirmacao, reembolso, pendencia
- informacao, desistencia, boas_vindas, lembrete, outro

### Endpoints (/api/contatos)
**Referência:**
- `GET /api/contatos/tipos` - Lista tipos de contato
- `GET /api/contatos/resultados` - Lista resultados
- `GET /api/contatos/motivos` - Lista motivos

**Estatísticas:**
- `GET /api/contatos/stats` - KPIs gerais de contatos
- `GET /api/contatos/retornos` - Lista retornos pendentes/atrasados

**CRUD:**
- `POST /api/contatos` - Registrar novo contato
- `GET /api/contatos/pedido/{pedido_id}` - Listar contatos de um pedido
- `GET /api/contatos/{id}` - Buscar contato
- `PUT /api/contatos/{id}` - Atualizar contato
- `POST /api/contatos/{id}/marcar-retorno` - Marcar retorno realizado
- `DELETE /api/contatos/{id}` - Excluir (admin only)


## Apoio Cognitivo - Meu Dia + Base de Conhecimento (2026-02-23) - NOVO!
Sistema de apoio cognitivo para organização pessoal e gestão de conhecimento.

### Meu Dia (Checklist Diário)
Página personalizada com:
- Saudação dinâmica (Bom dia/Boa tarde/Boa noite + nome do usuário)
- Cards de resumo: Tarefas do dia, Pendências abertas, Pedidos em andamento, Retornos pendentes
- Lista de tarefas com checkbox, categorias, prioridades e horários sugeridos
- Lembretes do dia
- Acesso rápido para módulos importantes
- Dica do dia

### Categorias de Tarefas
- `rotina` - Rotina Diária (azul)
- `pendencia` - Pendência (laranja)
- `lembrete` - Lembrete (roxo)
- `reuniao` - Reunião (verde)
- `outro` - Outro (cinza)

### Base de Conhecimento
Repositório de artigos e procedimentos com:
- Categorias: Procedimento, FAQ, Documento, Dica Rápida, Informação de Contato
- Busca por texto
- Filtro por categoria
- Artigos em destaque
- Contador de visualizações
- Renderização markdown simplificada

### Endpoints (/api/apoio)

**Meu Dia:**
- `GET /api/apoio/meu-dia` - Resumo completo do dia do usuário

**Tarefas:**
- `GET /api/apoio/tarefas` - Listar tarefas (com filtros: data, categoria, concluida)
- `POST /api/apoio/tarefas` - Criar tarefa
- `PUT /api/apoio/tarefas/{id}` - Atualizar tarefa
- `PATCH /api/apoio/tarefas/{id}/concluir` - Marcar/desmarcar como concluída
- `DELETE /api/apoio/tarefas/{id}` - Remover tarefa

**Lembretes:**
- `GET /api/apoio/lembretes` - Listar lembretes
- `POST /api/apoio/lembretes` - Criar lembrete
- `PATCH /api/apoio/lembretes/{id}/concluir` - Marcar como concluído
- `DELETE /api/apoio/lembretes/{id}` - Remover lembrete

**Base de Conhecimento:**
- `GET /api/apoio/conhecimento/categorias` - Listar categorias
- `GET /api/apoio/conhecimento` - Listar artigos (com filtros: categoria, busca, destaque)
- `GET /api/apoio/conhecimento/{id}` - Buscar artigo (incrementa visualizações)
- `POST /api/apoio/conhecimento` - Criar artigo (Admin only)
- `PUT /api/apoio/conhecimento/{id}` - Atualizar artigo (Admin only)
- `DELETE /api/apoio/conhecimento/{id}` - Remover artigo (Admin only)

### Páginas Frontend
- `/meu-dia` - MeuDiaPage.jsx
- `/base-conhecimento` - BaseConhecimentoPage.jsx

### Modelos de Dados (SQLAlchemy)
- `TarefaDiariaModel` - Tarefas do checklist diário
- `LembreteModel` - Lembretes personalizados
- `ArtigoConhecimentoModel` - Artigos da base de conhecimento

### Test Report
- `/app/test_reports/iteration_10.json` - 41/41 testes PASS (100%)
- `/app/backend/tests/test_apoio_cognitivo.py` - Suite de testes


## Painel de Conta do Usuário (2026-02-24) - COMPLETO! ✅
Sistema de gerenciamento de conta pessoal do usuário com log de atividades.

### Funcionalidades
- **Perfil:** Editar nome e email
- **Segurança:** Alterar senha (com validação da senha atual)
- **Atividades:** Log completo de auditoria das ações do usuário (NOVO!)

### Log de Atividades (2026-02-24) - NOVO!
Sistema de auditoria que registra automaticamente todas as ações do usuário:

**Tipos de Atividades Rastreadas:**
- `login` - Login no sistema
- `logout` - Logout do sistema  
- `criar_pedido` - Criação de solicitação de matrícula
- `atualizar_pedido` - Atualização de solicitação
- `criar_pendencia` - Criação de pendência documental
- `atualizar_pendencia` - Atualização de pendência
- `criar_reembolso` - Criação de solicitação de reembolso
- `atualizar_reembolso` - Atualização de reembolso
- `atribuir_demanda` - Atribuição de demanda a responsável
- `alterar_perfil` - Alteração de dados do perfil
- `alterar_senha` - Alteração de senha
- `exportar_totvs` - Exportação para TOTVS
- `importar_lote` - Importação de dados em lote

**Modelo de Dados (AtividadeUsuarioModel):**
- `id` - UUID
- `usuario_id` - ID do usuário
- `usuario_nome` - Nome do usuário
- `tipo` - Tipo da atividade
- `descricao` - Descrição legível
- `entidade_tipo` - Tipo da entidade (pedido, pendencia, etc)
- `entidade_id` - ID da entidade relacionada
- `entidade_nome` - Nome/identificador da entidade
- `detalhes` - JSON com detalhes adicionais
- `ip_address` - IP do usuário (opcional)
- `created_at` - Data/hora da ação

### Endpoints (/api/auth)
- `PUT /api/auth/me/perfil` - Atualizar dados do perfil (registra atividade)
- `PUT /api/auth/me/senha` - Alterar senha (registra atividade)
- `GET /api/auth/me/atividades` - Listar atividades com filtros
  - Query params: `limite` (1-100), `tipo` (filtro por tipo)
  - Retorna: `atividades`, `auditorias`, `pedidos_recentes`, `tipos_disponiveis`

### Página Frontend
- `/minha-conta` - ConfiguracaoContaPage.jsx
- **Aba Atividades:** Timeline visual com ícones coloridos, filtro por tipo, botão de atualizar
- **Retrocompatibilidade:** Exibe auditorias antigas do sistema legado

### Serviço de Atividades
- `/app/backend/src/services/atividade_service.py`
- Funções: `registrar_atividade()`, `listar_atividades_usuario()`, `get_tipos_atividade()`

### Test Report
- `/app/test_reports/iteration_11.json` - 21/21 backend + 100% frontend PASS


## Sistema de Atribuições/Chamados (2026-02-23) - NOVO!
Sistema de atribuição de demandas para atendentes específicos, similar a um sistema de chamados.

### Funcionalidades
- **Caixa de Entrada:** Lista todas as demandas atribuídas ao usuário logado
- **Atribuição:** Permite atribuir pedidos, pendências ou reembolsos a um responsável
- **Prioridades:** baixa, normal, alta, urgente
- **Filtros:** Por tipo (pedido/pendência/reembolso) e status
- **Notificação por Email:** (quando configurado) envia email ao responsável

### Campos adicionados aos modelos
- `responsavel_id` - ID do usuário responsável
- `responsavel_nome` - Nome do responsável
- `prioridade` - Prioridade da demanda

### Endpoints (/api/atribuicoes)
- `GET /api/atribuicoes/minha-caixa` - Lista demandas do usuário
- `GET /api/atribuicoes/resumo` - Resumo com contadores
- `POST /api/atribuicoes/atribuir` - Atribuir demanda a responsável
- `DELETE /api/atribuicoes/atribuir/{tipo}/{item_id}` - Remover atribuição
- `GET /api/atribuicoes/responsaveis` - Lista usuários disponíveis

### Página Frontend
- `/caixa-entrada` - CaixaEntradaPage.jsx


## Notificações por Email - SMTP Outlook (2026-02-23) - ESTRUTURA PRONTA!
Sistema de notificações por email via SMTP do Outlook/Microsoft 365.

### Configuração (.env)
```env
SMTP_SERVER="smtp.office365.com"
SMTP_PORT="587"
SMTP_USER="seu-email@fieb.org.br"
SMTP_PASSWORD="sua-app-password"
SMTP_FROM_NAME="SYNAPSE - Sistema de Matrículas"
FRONTEND_URL="https://operacional-hub.preview.emergentagent.com"
```

### Como obter App Password
1. Acesse https://account.microsoft.com/security
2. Vá em "Senhas de aplicativo" / "App passwords"
3. Gere uma nova senha para "SYNAPSE"
4. Use essa senha em SMTP_PASSWORD

### Serviço de Email
- `/app/backend/src/services/email_service.py`
- Envia notificações de atribuição com template HTML bonito
- Envia lembretes automáticos
- Funciona em background (não bloqueia requisições)


## Módulo de Regras de Negócio SENAI (2026-02-24) - NOVO!
Sistema completo de regras de negócio baseado nos procedimentos oficiais do SENAI (PG-SENAI.EP 003).

### Máquina de Estados Expandida
Fluxo principal: `INSCRICAO` → `ANALISE_DOCUMENTAL` → `DOCUMENTACAO_PENDENTE` (5d) → `APROVADO` → `AGUARDANDO_PAGAMENTO` → `MATRICULADO` → `EXPORTADO`

Status alternativos: `NAO_ATENDE_REQUISITO`, `CANCELADO`, `TRANCADO`, `TRANSFERIDO`

### Tipos de Curso Configurados
| Tipo | Idade | Escolaridade | Empresa | Docs |
|------|-------|--------------|---------|------|
| CAI_BAS | 14-21 | Fund. Incompleto | Sim | 9 |
| CAI_TEC | 14-21 | Médio Cursando | Sim | 7 |
| CHP | 16+ | Médio Completo | Não | 5 |
| TECNICO | 16+ | Médio Cursando | Não | 5 |
| CURTA_DURACAO | 16+ | - | Não | 2 |
| LIVRE | - | - | Não | 2 |

### Prazos Configurados
- Pendência documental: 5 dias
- Não atende requisito: Cancelamento imediato (0 dias)
- Pagamento após aprovação: 7 dias
- Matrícula web antes da aula: 4 horas
- Comunicação cancelamento turma: 48 horas
- Reembolso: 15 dias úteis

### Endpoints de Regras (/api/regras)

**Tipos de Curso:**
- `GET /api/regras/tipos-curso` - Lista tipos de curso com regras
- `GET /api/regras/tipos-curso/{tipo}` - Detalhes de um tipo
- `GET /api/regras/tipos-curso/{tipo}/documentos` - Documentos obrigatórios

**Validação de Pré-Requisitos:**
- `POST /api/regras/validar/idade` - Valida idade do aluno
- `POST /api/regras/validar/escolaridade` - Valida escolaridade
- `POST /api/regras/validar/documentos` - Valida documentos apresentados
- `POST /api/regras/validar/completo` - Validação completa (recomendado)

**Prazos e SLA:**
- `GET /api/regras/prazos` - Lista prazos configurados
- `POST /api/regras/prazos/pendencia` - Calcula prazo de pendência
- `POST /api/regras/prazos/pagamento` - Calcula prazo de pagamento
- `GET /api/regras/prazos/sla` - Calcula SLA do pedido

**Templates de Mensagem:**
- `GET /api/regras/templates` - Lista templates disponíveis
- `GET /api/regras/templates/email` - Lista templates de email
- `GET /api/regras/templates/whatsapp` - Lista templates de WhatsApp
- `POST /api/regras/templates/email/render` - Renderiza template de email
- `POST /api/regras/templates/whatsapp/render` - Renderiza template WhatsApp (com link wa.me)

**Auxiliares:**
- `GET /api/regras/escolaridades` - Lista níveis de escolaridade

### Templates de Mensagem Disponíveis

**Email:**
- `documentos_pendentes` - Solicitação de documentos
- `prazo_expirando` - Alerta de prazo
- `confirmacao_matricula` - Confirmação de matrícula
- `aguardando_pagamento` - Lembrete de pagamento
- `nao_atende_requisito` - Comunicado de reprovação

**WhatsApp:**
- `documentos_pendentes` - Cobrança de documentos
- `prazo_expirando` - Alerta urgente
- `confirmacao_matricula` - Boas-vindas
- `aguardando_pagamento` - Lembrete de pagamento
- `lembrete_documentos` - Lembrete amigável

### Componentes Frontend Novos
- `AlertaPrazo.jsx` - Badge/Card de alerta de prazo
- `ValidadorPreRequisitos.jsx` - Formulário de validação
- `TemplatesMensagem.jsx` - Gerador de mensagens

### Arquivos de Serviço
- `/app/backend/src/services/regras_negocio_service.py` - Validador e Calculador de Prazos
- `/app/backend/src/services/templates_mensagem_service.py` - Renderizador de Templates
- `/app/backend/src/routers/regras_negocio.py` - Endpoints REST

