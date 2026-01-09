# Sistema Central de Matrículas - SENAI CIMATEC

## Instalação Local (Windows)

### Pré-requisitos
- Python 3.10+
- Node.js 18+

---

## Backend (Terminal 1)

```powershell
cd C:\Dev\Gestao_Matriculas-main\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
mkdir data
uvicorn server:app --reload --port 8001
```

---

## Frontend (Terminal 2)

```powershell
cd C:\Dev\Gestao_Matriculas-main\frontend
copy .env.local.example .env
npm install
npm start
```

---

## Acessar

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8001/docs

### Credenciais
| Perfil | Email | Senha |
|--------|-------|-------|
| Admin | admin@senai.br | admin123 |
| Assistente | assistente@senai.br | assistente123 |
| Consultor | consultor@senai.br | consultor123 |
