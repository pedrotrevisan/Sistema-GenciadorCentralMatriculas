# SYNAPSE - Sistema Central de Matrículas SENAI CIMATEC

## Prompt de Contexto para IAs

Você está trabalhando em um sistema web completo chamado **SYNAPSE** (anteriormente "Sistema Central de Matrículas - CM") desenvolvido para o SENAI CIMATEC. O sistema foi criado para substituir processos manuais de gestão de matrículas, pendências documentais e reembolsos, evoluindo para um "Hub de Inteligência Operacional" com funcionalidades de apoio cognitivo.

---

## 🏗️ ARQUITETURA TÉCNICA

### Stack Tecnológico
- **Backend:** Python 3.11 + FastAPI (Clean Architecture)
- **Frontend:** React 18 + Vite + JavaScript
- **Estilização:** Tailwind CSS + Shadcn/UI
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **ORM:** SQLAlchemy (async)
- **Autenticação:** JWT (JSON Web Tokens)
- **Email:** Resend API

### Estrutura de Diretórios
```
/app
├── backend/
│   ├── src/
│   │   ├── domain/
│   │   │   └── entities/          # Entidades de domínio (Usuario, Pedido, etc.)
│   │   ├── infrastructure/
│   │   │   └── persistence/
│   │   │       ├── models.py      # Modelos SQLAlchemy
│   │   │       ├── database.py    # Configuração do banco
│   │   │       └── repositories/  # Repositórios
│   │   ├── routers/               # Endpoints da API
│   │   │   ├── auth.py
│   │   │   ├── cadastros.py
│   │   │   ├── pendencias.py
│   │   │   ├── reembolsos.py
│   │   │   ├── atribuicoes.py
│   │   │   ├── apoio_cognitivo.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── email_service.py   # Serviço de email (Resend)
│   │   └── application/
│   │       └── dtos/              # Data Transfer Objects
│   ├── server.py                  # Aplicação FastAPI principal
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                # Componentes Shadcn/UI
│   │   │   ├── DashboardLayout.jsx
│   │   │   ├── AtribuirResponsavelModal.jsx
│   │   │   ├── CobrarZap.jsx
│   │   │   ├── IndicadorSLA.jsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── KanbanPage.jsx
│   │   │   ├── CentralPendenciasPage.jsx
│   │   │   ├── ReembolsosPage.jsx
│   │   │   ├── MeuDiaPage.jsx
│   │   │   ├── BaseConhecimentoPage.jsx
│   │   │   ├── CaixaEntradaPage.jsx
│   │   │   ├── ConfiguracaoContaPage.jsx
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── api.js             # Cliente Axios
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx
│   │   └── App.js
│   ├── package.json
│   └── .env
└── data/
    └── database.db                # Banco SQLite
```

---

## 👥 PERFIS DE USUÁRIO

### Roles (Papéis)
1. **admin** - Acesso total ao sistema
2. **assistente** - Gestão de matrículas, pendências e reembolsos
3. **consultor** - Criação de solicitações de matrícula

### Credenciais de Teste
- Admin: `admin@senai.br` / `admin123`
- Assistente: `assistente@senai.br` / `assistente123`
- Consultor: `consultor@senai.br` / `consultor123`

---

## 📋 MÓDULOS IMPLEMENTADOS

### 1. Autenticação e Autorização
- Login com email/senha
- JWT com expiração configurável
- Proteção de rotas por role
- Middleware de autenticação

### 2. Gestão de Matrículas (Pedidos)
- **Máquina de Estados:** pendente → em_analise → documentacao_pendente → aprovado → realizado → exportado
- Vinculação com Curso, Projeto e Empresa
- Múltiplos alunos por pedido
- Número de protocolo automático (CM-YYYY-NNNN)
- Timeline de auditoria visual
- Exportação para TOTVS (Excel)

### 3. Kanban de Matrículas
- Drag & drop entre colunas (usando @dnd-kit)
- Colunas: Pendente, Em Análise, Doc. Pendente, Aprovado, Realizado, Exportado
- Indicador de SLA visual
- Busca e filtros
- Botão de atribuir responsável em cada card

### 4. Central de Pendências Documentais
- Lista de documentos pendentes por aluno
- Status: pendente, aguardando_aluno, em_analise, aprovado, rejeitado, reenvio_necessario
- Registro de contatos (telefone, email, WhatsApp)
- Histórico de contatos por pendência
- **Criação manual de pendência** (sem pedido pré-existente)
- **Importação em lote** via Excel/CSV
- Coluna de responsável atribuído

### 5. Gestão de Reembolsos
- Fluxo: aberto → aguardando_dados_bancarios → enviado_financeiro → pago
- Registro de dados bancários do aluno
- Templates de email para comunicação
- Suporte a menor de idade (responsável financeiro)
- Motivos: sem_escolaridade, sem_vaga, passou_bolsista, desistencia, outros

### 6. Dashboard de BI (Business Intelligence)
- Cards de resumo (Total, Taxa de Conversão, Pendências, Reembolsos)
- Gráfico de evolução de matrículas (últimos 6 meses)
- Gráfico de distribuição por status (pizza)
- Tabs: Visão Geral, Matrículas, Contatos, Documentos, Financeiro
- Filtro por período

### 7. Módulo de Cadastros
- **Cursos:** Nome, tipo (graduacao/pos_graduacao/tecnico/etc), modalidade, área, carga horária, duração, status
- **Projetos:** Nome, descrição, empresa vinculada, status
- **Empresas:** Nome, CNPJ, contato, email, telefone

### 8. Apoio Cognitivo ("Meu Dia")
- Saudação personalizada (Bom dia/Boa tarde/Boa noite + nome)
- Cards de resumo: Tarefas do dia, Pendências abertas, Pedidos em andamento, Retornos pendentes
- Checklist de tarefas diárias com categorias (rotina, pendencia, lembrete, reuniao)
- Lembretes personalizados
- Acesso rápido aos módulos
- Dica do dia

### 9. Base de Conhecimento
- Artigos com categorias: Procedimento, FAQ, Documento, Dica Rápida, Informação de Contato
- Busca por texto
- Artigos em destaque
- Contador de visualizações
- CRUD de artigos (admin only)

### 10. Sistema de Atribuições/Chamados
- **Caixa de Entrada:** Lista de demandas atribuídas ao usuário logado
- Atribuir responsável em: Pedidos, Pendências, Reembolsos
- Níveis de prioridade: urgente, alta, normal, baixa
- Filtros por tipo e status
- **Notificação por email** (via Resend) ao atribuir

### 11. Painel de Conta do Usuário
- Editar nome e email
- Alterar senha (com validação da senha atual)
- Histórico de atividades recentes

### 12. Log de Contatos
- Registro de interações com alunos
- Tipos: telefone, email, whatsapp, presencial
- Vinculação com pendência ou pedido
- Marcação de retorno necessário

### 13. Ferramentas de Produtividade
- **Cobrar no Zap:** Geração de mensagem para WhatsApp
- **Indicador SLA:** Visual de tempo desde criação
- **Atalhos de teclado:** Navegação rápida (G+K = Kanban, G+P = Pendências, etc.)

---

## 🗄️ MODELOS DE DADOS PRINCIPAIS

### Usuario
```python
- id: UUID
- nome: String
- email: String (unique)
- senha_hash: String
- role: Enum (admin, assistente, consultor)
- ativo: Boolean
- created_at, updated_at: DateTime
```

### Pedido (Matrícula)
```python
- id: UUID
- numero_protocolo: String (CM-YYYY-NNNN)
- consultor_id, consultor_nome
- curso_id, curso_nome
- projeto_id, projeto_nome
- empresa_id, empresa_nome
- vinculo_tipo: String (projeto, empresa, brasil_mais_produtivo)
- status: String
- responsavel_id, responsavel_nome  # Atribuição
- prioridade: String
- observacoes, motivo_rejeicao: Text
- created_at, updated_at: DateTime
```

### Aluno
```python
- id: UUID
- pedido_id: FK
- nome, cpf, rg, data_nascimento
- email, telefone, telefone_secundario
- endereco, numero, complemento, bairro, cidade, estado, cep
- escolaridade
- created_at, updated_at: DateTime
```

### Pendencia
```python
- id: UUID
- aluno_id, pedido_id: FK
- documento_codigo, documento_nome
- status: String
- responsavel_id, responsavel_nome
- prioridade: String
- observacoes, motivo_rejeicao
- criado_por_id, criado_por_nome
- created_at, updated_at, resolved_at: DateTime
```

### Reembolso
```python
- id: UUID
- aluno_nome, aluno_cpf, aluno_email, aluno_telefone
- aluno_menor_idade: Boolean
- curso, turma
- motivo, motivo_descricao
- reter_taxa: Boolean
- banco_* (dados bancários)
- responsavel_id, responsavel_nome
- prioridade: String
- status: String
- criado_por_id, criado_por_nome
- created_at, updated_at: DateTime
```

### TarefaDiaria (Apoio Cognitivo)
```python
- id: UUID
- usuario_id: FK
- titulo, descricao
- categoria: String (rotina, pendencia, lembrete, reuniao, outro)
- prioridade: Integer
- recorrente: Boolean
- horario_sugerido: String
- concluida: Boolean
- data_tarefa: Date
```

### ArtigoConhecimento
```python
- id: UUID
- titulo, conteudo, resumo
- categoria: String
- tags: String
- destaque: Boolean
- visualizacoes: Integer
- autor_id, autor_nome
- created_at, updated_at: DateTime
```

---

## 🔌 ENDPOINTS DA API (Principais)

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registro (admin)
- `GET /api/auth/me` - Dados do usuário logado
- `PUT /api/auth/me/perfil` - Atualizar perfil
- `PUT /api/auth/me/senha` - Alterar senha
- `GET /api/auth/me/atividades` - Atividades recentes

### Pedidos
- `GET /api/pedidos` - Listar pedidos (paginado)
- `POST /api/pedidos` - Criar pedido
- `GET /api/pedidos/{id}` - Detalhes do pedido
- `PUT /api/pedidos/{id}` - Atualizar pedido
- `PATCH /api/pedidos/{id}/status` - Alterar status
- `GET /api/pedidos/analytics` - Dashboard analytics
- `POST /api/pedidos/exportar-totvs` - Exportar para TOTVS

### Pendências
- `GET /api/pendencias` - Listar pendências
- `GET /api/pendencias/dashboard` - Dashboard
- `POST /api/pendencias/manual` - Criar pendência manual
- `POST /api/pendencias/importar/validar` - Validar importação
- `POST /api/pendencias/importar/executar` - Executar importação
- `PATCH /api/pendencias/{id}/status` - Alterar status

### Reembolsos
- `GET /api/reembolsos` - Listar
- `POST /api/reembolsos` - Criar
- `GET /api/reembolsos/dashboard` - Dashboard
- `POST /api/reembolsos/{id}/dados-bancarios` - Registrar dados bancários
- `PATCH /api/reembolsos/{id}/status` - Alterar status

### Atribuições
- `GET /api/atribuicoes/minha-caixa` - Caixa de entrada do usuário
- `GET /api/atribuicoes/resumo` - Resumo com contadores
- `POST /api/atribuicoes/atribuir` - Atribuir demanda
- `DELETE /api/atribuicoes/atribuir/{tipo}/{item_id}` - Remover atribuição
- `GET /api/atribuicoes/responsaveis` - Listar responsáveis

### Apoio Cognitivo
- `GET /api/apoio/meu-dia` - Resumo do dia
- `GET /api/apoio/tarefas` - Listar tarefas
- `POST /api/apoio/tarefas` - Criar tarefa
- `PATCH /api/apoio/tarefas/{id}/concluir` - Marcar concluída
- `GET /api/apoio/conhecimento` - Listar artigos
- `POST /api/apoio/conhecimento` - Criar artigo (admin)

### Cadastros
- `GET /api/cadastros/cursos` - Listar cursos
- `POST /api/cadastros/cursos` - Criar curso
- `GET /api/cadastros/projetos` - Listar projetos
- `GET /api/cadastros/empresas` - Listar empresas

---

## 🎨 PADRÕES DE UI/UX

### Cores Principais
- **Azul SENAI:** #004587 (cor primária)
- **Backgrounds:** Slate-50, White
- **Status:** Verde (sucesso), Amarelo (pendente), Vermelho (erro/urgente), Azul (em andamento)

### Componentes UI
- Shadcn/UI como base
- Cards com sombras suaves
- Badges coloridos por status
- Modais para ações
- Toast notifications (sonner)
- Tabelas responsivas com paginação

### Layout
- Sidebar fixa à esquerda
- Header com logo e dropdown do usuário
- Área de conteúdo principal centralizada
- Responsivo para diferentes tamanhos de tela

---

## 🔧 CONFIGURAÇÕES DE AMBIENTE

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db  # ou SQLite
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
CORS_ORIGINS=*
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
FRONTEND_URL=https://your-domain.com
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://your-api-domain.com
```

---

## 📝 NOTAS IMPORTANTES

1. **Banco de Dados:** O sistema usa SQLite para desenvolvimento (portátil) e pode usar PostgreSQL em produção.

2. **Autenticação:** Todas as rotas (exceto login) requerem token JWT no header `Authorization: Bearer <token>`.

3. **Roles:** O sistema verifica permissões por role. Admin tem acesso total, assistente pode gerenciar tudo exceto usuários, consultor só cria pedidos.

4. **Emails:** O serviço de email usa Resend API. No plano gratuito, só envia para o email cadastrado na conta Resend.

5. **Hot Reload:** Backend e frontend têm hot reload habilitado para desenvolvimento.

6. **Clean Architecture:** O backend segue princípios de Clean Architecture com separação de domínio, infraestrutura e aplicação.

---

## 🚀 PRÓXIMAS FUNCIONALIDADES PLANEJADAS

1. Filtros por data nas listagens
2. Badge de notificação na Caixa de Entrada
3. Histórico de atribuições
4. Controle orçamentário para projetos
5. Upload de documentos do aluno
6. Integração com API de CEP (ViaCEP)
7. Notificações push
8. Relatórios exportáveis em PDF

---

Este é o contexto completo do sistema SYNAPSE. Use estas informações para entender a estrutura, funcionalidades e padrões do projeto ao realizar qualquer modificação ou adição de features.
