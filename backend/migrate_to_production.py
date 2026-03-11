#!/usr/bin/env python3
"""
Script de migração de dados: Dev MongoDB → Produção
Exporta os dados do MongoDB de desenvolvimento e os importa na produção.

Uso:
  python3 migrate_to_production.py

Variáveis de ambiente esperadas (ou altere as constantes abaixo):
  DEV_API_URL   - URL da API de desenvolvimento
  PROD_API_URL  - URL da API de produção
  PROD_EMAIL    - Email do admin de produção
  PROD_SENHA    - Senha do admin de produção
"""
import pymongo
import requests
import json
import sys
import time

# =============================================
# CONFIGURAÇÃO
# =============================================
DEV_MONGO_URL = "mongodb://localhost:27017"
DEV_DB_NAME = "synapse"

PROD_API_URL = "https://synapse.pedrotrevisan.dev.br"
PROD_EMAIL = "cristiane.mendes@fieb.org.br"
PROD_SENHA = "Senai@2026"

BATCH_SIZE = 200  # Documentos por requisição

# Coleções para migrar (em ordem de dependência)
COLLECTIONS_TO_MIGRATE = [
    "tipos_documento",
    "cursos",
    "projetos",
    "empresas",
    "usuarios",
    "painel_turmas",
    "pedidos",
    "alunos",
    "reembolsos",
    "pendencias",
    "chamados_sgc",
    "artigos_conhecimento",
]


def get_prod_token():
    """Obtém token de autenticação na produção."""
    print(f"\n[AUTH] Autenticando em {PROD_API_URL}...")
    resp = requests.post(
        f"{PROD_API_URL}/api/auth/login",
        json={"email": PROD_EMAIL, "senha": PROD_SENHA},
        timeout=30
    )
    if resp.status_code != 200:
        print(f"  ERRO ao autenticar: {resp.status_code} - {resp.text[:200]}")
        sys.exit(1)
    
    token = resp.json().get("token")
    if not token:
        print(f"  ERRO: token não encontrado na resposta: {resp.text[:200]}")
        sys.exit(1)
    
    print(f"  OK! Token obtido.")
    return token


def export_collection(col_name, db):
    """Exporta uma coleção do MongoDB de desenvolvimento."""
    col = db[col_name]
    docs = list(col.find({}, {"_id": 0}))
    print(f"  Exportando {col_name}: {len(docs)} documentos")
    return docs


def migrate_collection(col_name, docs, token, clear_first=True):
    """Migra uma coleção para a produção em batches."""
    if not docs:
        print(f"  {col_name}: 0 documentos, pulando...")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    total_inserted = 0
    total_updated = 0
    total_errors = 0
    
    # Divide em batches
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(docs) + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Primeiro batch: limpa a coleção
        params = {"clear_first": "true" if (clear_first and i == 0) else "false"}
        
        try:
            resp = requests.post(
                f"{PROD_API_URL}/api/admin/seed/{col_name}",
                json=batch,
                headers=headers,
                params=params,
                timeout=120
            )
            
            if resp.status_code == 200:
                result = resp.json()
                total_inserted += result.get("inserted", 0)
                total_updated += result.get("updated", 0)
                errs = result.get("errors", [])
                total_errors += len(errs)
                print(f"  {col_name} batch {batch_num}/{total_batches}: "
                      f"+{result.get('inserted',0)} inseridos, "
                      f"~{result.get('updated',0)} atualizados"
                      + (f", {len(errs)} erros" if errs else ""))
                if errs:
                    for e in errs[:3]:
                        print(f"    Erro: {e}")
            else:
                print(f"  ERRO batch {batch_num}: {resp.status_code} - {resp.text[:200]}")
                total_errors += len(batch)
        except Exception as e:
            print(f"  EXCEÇÃO batch {batch_num}: {e}")
            total_errors += len(batch)
        
        # Pequeno delay entre batches
        if total_batches > 1:
            time.sleep(0.5)
    
    print(f"  TOTAL {col_name}: {total_inserted} inseridos, {total_updated} atualizados, {total_errors} erros")


def check_prod_status(token):
    """Verifica o status do banco de produção."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{PROD_API_URL}/api/admin/seed/status",
        headers=headers,
        timeout=30
    )
    if resp.status_code == 200:
        data = resp.json()
        print("\n=== STATUS DO BANCO DE PRODUÇÃO ===")
        for col, count in data.get("collections", {}).items():
            print(f"  {col}: {count} documentos")
    else:
        print(f"Erro ao verificar status: {resp.status_code}")


def main():
    print("=" * 60)
    print("SYNAPSE - Migração de Dados Dev → Produção")
    print("=" * 60)
    
    # Conecta ao MongoDB de desenvolvimento
    print(f"\n[MONGO] Conectando ao MongoDB local ({DEV_MONGO_URL})...")
    client = pymongo.MongoClient(DEV_MONGO_URL)
    dev_db = client[DEV_DB_NAME]
    
    # Verifica coleções disponíveis
    available = dev_db.list_collection_names()
    print(f"  Coleções disponíveis: {available}")
    
    # Obtém token de produção
    prod_token = get_prod_token()
    
    # Verifica status antes
    check_prod_status(prod_token)
    
    print("\n=== INICIANDO MIGRAÇÃO ===")
    
    for col_name in COLLECTIONS_TO_MIGRATE:
        if col_name not in available:
            print(f"\n[SKIP] {col_name} não existe no banco de desenvolvimento")
            continue
        
        print(f"\n[{col_name.upper()}]")
        docs = export_collection(col_name, dev_db)
        migrate_collection(col_name, docs, prod_token, clear_first=True)
    
    # Verifica status depois
    check_prod_status(prod_token)
    
    print("\n=== MIGRAÇÃO CONCLUÍDA ===")
    client.close()


if __name__ == "__main__":
    main()
