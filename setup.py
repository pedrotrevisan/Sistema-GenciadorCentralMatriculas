#!/usr/bin/env python3
"""
🚀 SYNAPSE - Script de Setup Automático
Sistema Central de Matrículas SENAI CIMATEC
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    print("\n" + "="*60)
    print("🚀 SYNAPSE - Setup Automático")
    print("   Sistema Central de Matrículas SENAI CIMATEC")
    print("="*60 + "\n")

def print_step(step, message):
    print(f"\n[{step}/6] {message}...")

def check_python():
    """Verifica versão do Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário!")
        print(f"   Versão atual: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")

def check_node():
    """Verifica se Node.js está instalado"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"✅ Node.js {version} detectado")
        return True
    except FileNotFoundError:
        print("⚠️  Node.js não encontrado")
        print("   Baixe em: https://nodejs.org/")
        return False

def install_backend_deps():
    """Instala dependências do backend"""
    print("\n📦 Instalando dependências do backend...")
    backend_dir = Path(__file__).parent / 'backend'
    
    try:
        # Instalar requirements
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            cwd=backend_dir,
            check=True
        )
        print("✅ Dependências do backend instaladas!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def install_frontend_deps():
    """Instala dependências do frontend"""
    print("\n📦 Instalando dependências do frontend...")
    frontend_dir = Path(__file__).parent / 'frontend'
    
    # Verificar se yarn está disponível, senão usar npm
    try:
        subprocess.run(['yarn', '--version'], capture_output=True, check=True)
        cmd = ['yarn', 'install']
        print("   Usando Yarn...")
    except (FileNotFoundError, subprocess.CalledProcessError):
        cmd = ['npm', 'install']
        print("   Usando NPM...")
    
    try:
        subprocess.run(cmd, cwd=frontend_dir, check=True)
        print("✅ Dependências do frontend instaladas!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def setup_database():
    """Configura banco de dados SQLite"""
    print("\n🗄️  Configurando banco de dados...")
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / 'database.db'
    if db_path.exists():
        print(f"✅ Banco de dados já existe: {db_path}")
    else:
        print(f"✅ Diretório criado: {data_dir}")
        print("   Banco será criado automaticamente na primeira execução")
    
    return True

def check_env_file():
    """Verifica arquivo .env"""
    print("\n⚙️  Verificando configurações...")
    backend_dir = Path(__file__).parent / 'backend'
    env_file = backend_dir / '.env'
    
    if env_file.exists():
        print(f"✅ Arquivo .env encontrado")
    else:
        print("⚠️  Arquivo .env não encontrado (usando configurações padrão)")
    
    return True

def print_success():
    print("\n" + "="*60)
    print("✅ SETUP CONCLUÍDO COM SUCESSO!")
    print("="*60)
    print("\n📋 Próximos passos:\n")
    
    if platform.system() == 'Windows':
        print("   1. Execute: start.bat")
        print("   2. Ou manualmente:")
        print("      - Backend:  cd backend && uvicorn server:app --reload")
        print("      - Frontend: cd frontend && yarn dev")
    else:
        print("   1. Execute: ./start.sh")
        print("   2. Ou manualmente:")
        print("      - Backend:  cd backend && uvicorn server:app --reload")
        print("      - Frontend: cd frontend && yarn dev")
    
    print("\n🌐 URLs:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend:  http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    
    print("\n👤 Credenciais padrão:")
    print("   - Admin:      admin@senai.br / admin123")
    print("   - Assistente: assistente@senai.br / assistente123")
    print("   - Consultor:  consultor@senai.br / consultor123")
    
    print("\n📚 Documentação: /app/README_INSTALL.md")
    print("="*60 + "\n")

def main():
    print_header()
    
    # 1. Verificar Python
    print_step(1, "Verificando Python")
    check_python()
    
    # 2. Verificar Node.js
    print_step(2, "Verificando Node.js")
    has_node = check_node()
    
    # 3. Instalar dependências backend
    print_step(3, "Instalando dependências do backend")
    if not install_backend_deps():
        print("\n⚠️  Setup parcialmente concluído (backend com problemas)")
        sys.exit(1)
    
    # 4. Instalar dependências frontend
    if has_node:
        print_step(4, "Instalando dependências do frontend")
        install_frontend_deps()
    else:
        print_step(4, "Pulando frontend (Node.js não instalado)")
    
    # 5. Setup banco de dados
    print_step(5, "Configurando banco de dados")
    setup_database()
    
    # 6. Verificar .env
    print_step(6, "Verificando configurações")
    check_env_file()
    
    # Sucesso!
    print_success()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)
