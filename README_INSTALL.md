# 🚀 SYNAPSE - Guia de Instalação Rápida

## Sistema Central de Matrículas SENAI CIMATEC

---

## ⚡ Instalação Ultra Rápida

### Windows
```batch
# 1. Duplo-clique em: setup.bat
# 2. Duplo-clique em: start.bat
# 3. Acesse: http://localhost:3000
```

### Linux/Mac
```bash
# 1. Dar permissão de execução
chmod +x setup.sh start.sh

# 2. Executar setup
./setup.sh

# 3. Iniciar sistema
./start.sh

# 4. Acessar: http://localhost:3000
```

---

## 📋 Pré-requisitos

### Obrigatório
- **Python 3.8+** - [Download](https://python.org)
- **Node.js 16+** - [Download](https://nodejs.org)

### Opcional (para melhor desempenho OCR)
- **Tesseract OCR** - Já funciona sem, mas melhora a precisão
  - Windows: `choco install tesseract` ou [download manual](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt install tesseract-ocr tesseract-ocr-por`
  - Mac: `brew install tesseract tesseract-lang`

---

## 🗄️ Banco de Dados

**SQLite** é usado por padrão (zero configuração!).

O arquivo do banco fica em: `/data/database.db`

### Para usar PostgreSQL (opcional)

1. Edite `backend/.env`:
```env
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
```

2. Reinicie o backend

---

## 🔐 Credenciais Padrão

| Usuário | Email | Senha |
|---------|-------|-------|
| Admin | admin@senai.br | admin123 |
| Assistente | assistente@senai.br | assistente123 |
| Consultor | consultor@senai.br | consultor123 |

---

## 🌐 URLs do Sistema

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentação da API:** http://localhost:8000/docs
- **Documentação Alternativa:** http://localhost:8000/redoc

---

## 🔧 Configuração do OCR

O sistema usa **EasyOCR por padrão** (funciona offline, sem configuração).

### Trocar engine de OCR

Edite `backend/.env`:

```env
# Opções: easyocr, tesseract, google_vision
OCR_ENGINE="easyocr"
```

### Usar Google Cloud Vision (melhor precisão)

1. Obtenha credenciais do Google Cloud
2. Edite `backend/.env`:
```env
OCR_ENGINE="google_vision"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
GOOGLE_CLOUD_PROJECT_ID="your-project-id"
```

---

## 📦 Estrutura do Projeto

```
SYNAPSE/
├── setup.py              # Setup automático
├── setup.bat             # Setup Windows
├── setup.sh              # Setup Linux/Mac
├── start.bat             # Iniciar Windows
├── start.sh              # Iniciar Linux/Mac
├── backend/              # API FastAPI
│   ├── server.py
│   ├── requirements.txt
│   ├── .env
│   └── src/
├── frontend/             # Interface React
│   ├── package.json
│   └── src/
├── data/                 # Banco SQLite
│   └── database.db
└── README_INSTALL.md     # Este arquivo
```

---

## 🐛 Problemas Comuns

### "Python não encontrado"
- Instale Python 3.8+ em [python.org](https://python.org)
- No Windows, marque "Add Python to PATH" durante instalação

### "Node.js não encontrado"
- Instale Node.js em [nodejs.org](https://nodejs.org)
- Versão LTS recomendada

### "Porta 8000 ou 3000 em uso"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### "Erro ao instalar dependências Python"
```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar com usuário
pip install -r backend/requirements.txt --user
```

### "Erro EasyOCR na primeira execução"
É normal! O EasyOCR baixa modelos na primeira vez (pode demorar 2-3 minutos).

---

## 📊 Backup do Banco de Dados

### Fazer backup
```bash
# Windows
copy data\database.db data\database_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%.db

# Linux/Mac
cp data/database.db data/database_backup_$(date +%Y%m%d).db
```

### Restaurar backup
```bash
# Windows
copy data\database_backup_YYYYMMDD.db data\database.db

# Linux/Mac
cp data/database_backup_YYYYMMDD.db data/database.db
```

---

## 🚀 Deploy em Produção

### Backend
```bash
cd backend
gunicorn server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
yarn build
yarn start
```

---

## 📞 Suporte

- **Documentação completa:** `/docs`
- **API Docs:** http://localhost:8000/docs

---

## 📝 Licença

Sistema desenvolvido para SENAI CIMATEC.

---

**Última atualização:** Fevereiro 2025
