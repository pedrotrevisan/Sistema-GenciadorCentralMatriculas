"""
Endpoint temporário de seed/migração de dados para produção.
Usado para popular o banco MongoDB de produção com dados do ambiente de desenvolvimento.
ATENÇÃO: Apenas admins podem usar estes endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, List
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/admin/seed", tags=["Seed"])


def require_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado: requer role admin")
    return current_user


@router.post("/{collection}")
async def seed_collection(
    collection: str,
    documents: List[Any],
    clear_first: bool = False,
    current_user=Depends(require_admin)
):
    """
    Popula uma coleção MongoDB com os documentos fornecidos.
    Se clear_first=True, limpa a coleção antes de inserir.
    Faz upsert baseado no campo 'id'.
    """
    ALLOWED_COLLECTIONS = [
        "usuarios", "pedidos", "reembolsos", "pendencias", "cursos",
        "alunos", "projetos", "empresas", "painel_turmas",
        "chamados_sgc", "tipos_documento", "artigos_conhecimento",
        "tarefas_diarias", "atividades_usuario"
    ]

    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Coleção não permitida: {collection}")

    col = db[collection]

    if clear_first:
        await col.delete_many({})

    inserted = 0
    updated = 0
    errors = []

    for doc in documents:
        try:
            # Remove _id se existir (campo MongoDB interno)
            doc.pop("_id", None)

            if "id" in doc and doc["id"]:
                result = await col.replace_one({"id": doc["id"]}, doc, upsert=True)
                if result.upserted_id:
                    inserted += 1
                else:
                    updated += 1
            else:
                await col.insert_one(doc)
                inserted += 1
        except Exception as e:
            errors.append(str(e)[:100])

    return {
        "collection": collection,
        "inserted": inserted,
        "updated": updated,
        "errors": errors[:10] if errors else [],
        "total": len(documents)
    }


@router.get("/status")
async def seed_status(
    current_user=Depends(require_admin)
):
    """Retorna a contagem de documentos em cada coleção."""
    collections = [
        "usuarios", "pedidos", "reembolsos", "pendencias", "cursos",
        "alunos", "projetos", "empresas", "painel_turmas",
        "chamados_sgc", "tipos_documento"
    ]
    status = {}
    for col_name in collections:
        count = await db[col_name].count_documents({})
        status[col_name] = count
    return {"collections": status}
