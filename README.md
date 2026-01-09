# Sistema Central de Matrículas - SENAI CIMATEC

## Guia de Instalação Local

### Pré-requisitos
- Python 3.10 ou superior
- Node.js 18 ou superior
- Git

---

## 1. Clone ou Baixe o Projeto

```bash
# Se tiver Git instalado
git clone <url-do-repositorio>
cd app

# Ou baixe o ZIP pelo botão "Download" no Emergent
```

---

## 2. Configurar o Backend

### 2.1 Criar ambiente virtual Python
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2.2 Instalar dependências
```bash
pip install -r requirements.txt
```

### 2.3 Criar arquivo .env
Crie um arquivo `.env` na pasta `backend/` com:
```env
DATABASE_URL=sqlite+aiosqlite:///./data/matriculas.db
JWT_SECRET_KEY=sua-chave-secreta-aqui-mude-em-producao
CORS_ORIGINS=http://localhost:3000
```

### 2.4 Criar pasta de dados
```bash
mkdir data
```

### 2.5 Executar o Backend
```bash
uvicorn server:app --reload --port 8001
```

O backend estará rodando em: **http://localhost:8001**

Documentação da API: **http://localhost:8001/docs**

---

## 3. Configurar o Frontend

### 3.1 Abrir novo terminal e ir para pasta frontend
```bash
cd frontend
```

### 3.2 Instalar dependências
```bash
# Usando npm
npm install

# OU usando yarn (recomendado)
yarn install
```

### 3.3 Criar arquivo .env
Crie um arquivo `.env` na pasta `frontend/` com:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 3.4 Executar o Frontend
```bash
# Usando npm
npm start

# OU usando yarn
yarn start
```

O frontend estará rodando em: **http://localhost:3000**

---

## 4. Acessar o Sistema

Abra o navegador em: **http://localhost:3000**

### Credenciais de Acesso:
| Perfil      | Email                  | Senha         |
|-------------|------------------------|---------------|
| Admin       | admin@senai.br         | admin123      |
| Assistente  | assistente@senai.br    | assistente123 |
| Consultor   | consultor@senai.br     | consultor123  |

---

## 5. Estrutura do Projeto

```
app/
├── backend/
│   ├── data/                  # Banco SQLite (criado automaticamente)
│   ├── src/
│   │   ├── domain/            # Entidades, Value Objects, Interfaces
│   │   ├── application/       # Use Cases, DTOs
│   │   └── infrastructure/    # Repositórios, Exportadores, Security
│   ├── server.py              # Aplicação FastAPI
│   ├── requirements.txt       # Dependências Python
│   └── .env                   # Configurações
│
└── frontend/
    ├── src/
    │   ├── components/        # Componentes React
    │   ├── pages/             # Páginas da aplicação
    │   ├── contexts/          # Context API (Auth)
    │   └── services/          # API client
    ├── package.json           # Dependências Node
    └── .env                   # Configurações
```

---

## 6. Comandos Úteis

### Backend
```bash
# Executar em modo desenvolvimento
uvicorn server:app --reload --port 8001

# Executar em produção
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
# Desenvolvimento
npm start

# Build para produção
npm run build
```

---

## 7. Solução de Problemas

### Erro: "Module not found"
```bash
# Certifique-se que está no ambiente virtual (backend)
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstale as dependências
pip install -r requirements.txt
```

### Erro: "CORS blocked"
Verifique se o arquivo `.env` do backend tem:
```env
CORS_ORIGINS=http://localhost:3000
```

### Erro: "Cannot connect to backend"
Verifique se o arquivo `.env` do frontend tem:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Banco de dados vazio
O banco é criado automaticamente na primeira execução. Os usuários padrão são criados automaticamente.

---

## 8. Tecnologias Utilizadas

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (async)
- SQLite + aiosqlite
- Pydantic
- JWT (python-jose)
- openpyxl (exportação Excel)

### Frontend
- React 18
- Tailwind CSS
- Shadcn/UI
- React Router
- Axios

---

## Suporte

Em caso de dúvidas, verifique:
1. Se ambos os serviços estão rodando (backend na porta 8001, frontend na porta 3000)
2. Se os arquivos `.env` estão configurados corretamente
3. Se todas as dependências foram instaladas
