"""Router Painel de Vagas - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/painel-vagas", tags=["Painel de Vagas"])


@router.get("/periodos")
async def listar_periodos(current_user: Usuario = Depends(get_current_user)):
    # Combina períodos das turmas existentes com períodos vazios registrados
    periodos_turmas = await db.painel_turmas.distinct("periodo_letivo", {"periodo_letivo": {"$ne": None}})
    periodos_vazios_docs = await db.periodos_letivos.find({}, {"periodo": 1, "_id": 0}).to_list(100)
    periodos_vazios = [p["periodo"] for p in periodos_vazios_docs if p.get("periodo")]
    
    # Une e remove duplicatas
    todos_periodos = list(set(periodos_turmas + periodos_vazios))
    todos_periodos.sort(reverse=True)
    return {"periodos": todos_periodos}


@router.get("/dashboard")
async def dashboard_vagas(periodo: Optional[str] = None, current_user: Usuario = Depends(get_current_user)):
    query = {}
    if periodo:
        query["periodo_letivo"] = periodo

    turmas = await db.painel_turmas.find(query, {"_id": 0}).to_list(1000)
    total_turmas = len(turmas)
    total_vagas = sum(t.get("vagas_totais", 0) for t in turmas)
    total_ocupadas = sum(t.get("vagas_ocupadas", 0) for t in turmas)
    turmas_lotando = sum(1 for t in turmas if t.get("vagas_totais", 0) > 0 and t.get("vagas_ocupadas", 0) >= t.get("vagas_totais", 0) * 0.9)

    # Por curso
    cursos_map = {}
    for t in turmas:
        c = t.get("nome_curso", "")
        if c not in cursos_map:
            cursos_map[c] = {"vagas": 0, "ocupadas": 0}
        cursos_map[c]["vagas"] += t.get("vagas_totais", 0)
        cursos_map[c]["ocupadas"] += t.get("vagas_ocupadas", 0)
    por_curso = [{"curso": k, "vagas_totais": v["vagas"], "vagas_ocupadas": v["ocupadas"],
                  "vagas_disponiveis": v["vagas"] - v["ocupadas"],
                  "percentual": round((v["ocupadas"] / v["vagas"] * 100) if v["vagas"] > 0 else 0, 1)}
                 for k, v in sorted(cursos_map.items())]

    # Por turno
    turno_map = {}
    for t in turmas:
        tr = t.get("turno", "")
        if tr not in turno_map:
            turno_map[tr] = {"vagas": 0, "ocupadas": 0}
        turno_map[tr]["vagas"] += t.get("vagas_totais", 0)
        turno_map[tr]["ocupadas"] += t.get("vagas_ocupadas", 0)
    por_turno = [{"turno": k, "vagas_totais": v["vagas"], "vagas_ocupadas": v["ocupadas"],
                  "percentual": round((v["ocupadas"] / v["vagas"] * 100) if v["vagas"] > 0 else 0, 1)}
                 for k, v in turno_map.items()]

    # Alertas
    alertas = []
    for t in turmas:
        vagas = t.get("vagas_totais", 0)
        ocupadas = t.get("vagas_ocupadas", 0)
        if vagas > 0 and ocupadas >= vagas * 0.85:
            alertas.append({
                "codigo": t.get("codigo_turma"), "curso": t.get("nome_curso"),
                "turno": t.get("turno"), "vagas_totais": vagas, "vagas_ocupadas": ocupadas,
                "vagas_disponiveis": vagas - ocupadas,
                "percentual": round((ocupadas / vagas * 100), 1),
                "status": "lotado" if ocupadas >= vagas else "lotando"
            })
    alertas.sort(key=lambda x: x["percentual"], reverse=True)

    return {
        "resumo": {
            "total_turmas": total_turmas, "total_vagas": total_vagas,
            "total_ocupadas": total_ocupadas, "vagas_disponiveis": total_vagas - total_ocupadas,
            "percentual_ocupacao": round((total_ocupadas / total_vagas * 100) if total_vagas > 0 else 0, 1),
            "turmas_lotando": turmas_lotando
        },
        "por_curso": por_curso, "por_turno": por_turno, "alertas": alertas[:10]
    }


@router.get("/turmas")
async def listar_turmas_painel(periodo: Optional[str] = None, turno: Optional[str] = None,
                                busca: Optional[str] = None, current_user: Usuario = Depends(get_current_user)):
    query = {}
    if periodo:
        query["periodo_letivo"] = periodo
    if turno:
        query["turno"] = turno
    if busca:
        query["$or"] = [{"nome_curso": {"$regex": busca, "$options": "i"}},
                        {"codigo_turma": {"$regex": busca, "$options": "i"}}]

    docs = await db.painel_turmas.find(query, {"_id": 0}).sort([("nome_curso", 1), ("turno", 1)]).to_list(1000)
    turmas = []
    for t in docs:
        vagas = t.get("vagas_totais", 0)
        ocupadas = t.get("vagas_ocupadas", 0)
        t["vagas_disponiveis"] = vagas - ocupadas
        t["percentual"] = round((ocupadas / vagas * 100) if vagas > 0 else 0, 1)
        t["status_ocupacao"] = "lotado" if ocupadas >= vagas else ("lotando" if ocupadas >= vagas * 0.85 else "disponivel")
        turmas.append(t)
    return {"turmas": turmas, "total": len(turmas)}


@router.post("/turmas")
async def criar_turma_painel(codigo_turma: str, nome_curso: str, turno: str,
                              vagas_totais: int, vagas_ocupadas: int = 0,
                              periodo_letivo: str = "2026.1", modalidade: str = "CHP",
                              current_user: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.painel_turmas.find_one({"codigo_turma": codigo_turma})
    if existing:
        await db.painel_turmas.update_one({"codigo_turma": codigo_turma}, {"$set": {
            "nome_curso": nome_curso, "turno": turno, "vagas_totais": vagas_totais,
            "vagas_ocupadas": vagas_ocupadas, "periodo_letivo": periodo_letivo,
            "modalidade": modalidade, "updated_at": now
        }})
        return {"message": "Turma atualizada", "id": existing["id"]}
    else:
        turma_id = str(uuid.uuid4())
        await db.painel_turmas.insert_one({
            "id": turma_id, "codigo_turma": codigo_turma, "nome_curso": nome_curso,
            "turno": turno, "vagas_totais": vagas_totais, "vagas_ocupadas": vagas_ocupadas,
            "periodo_letivo": periodo_letivo, "modalidade": modalidade, "status": "aberto",
            "created_at": now, "updated_at": now
        })
        return {"message": "Turma criada", "id": turma_id}


@router.put("/turmas/{turma_id}/ocupacao")
async def atualizar_ocupacao(turma_id: str, vagas_ocupadas: int, current_user: Usuario = Depends(get_current_user)):
    result = await db.painel_turmas.update_one({"id": turma_id}, {"$set": {
        "vagas_ocupadas": vagas_ocupadas, "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    if result.matched_count == 0:
        raise HTTPException(404, "Turma não encontrada")
    return {"message": "Ocupação atualizada"}


@router.delete("/turmas/{turma_id}")
async def deletar_turma(turma_id: str, current_user: Usuario = Depends(get_current_user)):
    if current_user.role.value not in ("admin",):
        raise HTTPException(403, "Sem permissão")
    result = await db.painel_turmas.delete_one({"id": turma_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Turma não encontrada")
    return {"message": "Turma deletada"}


@router.post("/importar-cimatec-2026")
async def importar_cursos_cimatec(current_user: Usuario = Depends(get_current_user)):
    cursos = [
        {"codigo": "B101622", "nome": "Técnico em Mecânica", "turno": "NOTURNO", "vagas": 40, "ocupadas": 26},
        {"codigo": "B101623", "nome": "Técnico em Eletrotécnica", "turno": "NOTURNO", "vagas": 42, "ocupadas": 16},
        {"codigo": "B101625", "nome": "Técnico em Desenvolvimento de Sistemas", "turno": "NOTURNO", "vagas": 40, "ocupadas": 12},
        {"codigo": "B101626", "nome": "Técnico em Multimídia", "turno": "NOTURNO", "vagas": 40, "ocupadas": 6},
        {"codigo": "B101627", "nome": "Técnico em Logística", "turno": "NOTURNO", "vagas": 42, "ocupadas": 1},
        {"codigo": "B101628", "nome": "Técnico em Mecatrônica", "turno": "NOTURNO", "vagas": 42, "ocupadas": 0},
        {"codigo": "B101629", "nome": "Técnico em Biotecnologia", "turno": "MATUTINO", "vagas": 30, "ocupadas": 1},
        {"codigo": "B101630", "nome": "Técnico em Petroquímica", "turno": "NOTURNO", "vagas": 40, "ocupadas": 1},
        {"codigo": "B101631", "nome": "Técnico em Redes de Computadores", "turno": "NOTURNO", "vagas": 40, "ocupadas": 1},
        {"codigo": "B101632", "nome": "Técnico em Manutenção Automotiva", "turno": "NOTURNO", "vagas": 42, "ocupadas": 1},
        {"codigo": "CQP102885", "nome": "Mecânico de Usinagem Convencional", "turno": "MATUTINO", "vagas": 40, "ocupadas": 28},
    ]
    importados, atualizados = 0, 0
    now = datetime.now(timezone.utc).isoformat()
    for c in cursos:
        existing = await db.painel_turmas.find_one({"codigo_turma": c["codigo"]})
        if existing:
            await db.painel_turmas.update_one({"codigo_turma": c["codigo"]}, {"$set": {
                "nome_curso": c["nome"], "turno": c["turno"], "vagas_totais": c["vagas"],
                "vagas_ocupadas": c["ocupadas"], "updated_at": now
            }})
            atualizados += 1
        else:
            await db.painel_turmas.insert_one({
                "id": str(uuid.uuid4()), "codigo_turma": c["codigo"], "nome_curso": c["nome"],
                "turno": c["turno"], "vagas_totais": c["vagas"], "vagas_ocupadas": c["ocupadas"],
                "periodo_letivo": "2026.1", "modalidade": "CHP", "status": "aberto",
                "created_at": now, "updated_at": now
            })
            importados += 1
    return {"message": "Cursos CIMATEC importados!", "importados": importados, "atualizados": atualizados, "total": len(cursos)}


@router.post("/duplicar-periodo")
async def duplicar_turmas_periodo(
    periodo_origem: str = Query(None), periodo_destino: str = Query(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Duplicar turmas de um período ou criar um período vazio.
    Se periodo_origem for None ou vazio, apenas registra o novo período.
    """
    if current_user.role.value not in ("admin",):
        raise HTTPException(403, "Apenas administradores podem criar/duplicar períodos")

    existing = await db.painel_turmas.count_documents({"periodo_letivo": periodo_destino})
    if existing > 0:
        raise HTTPException(409, f"O período {periodo_destino} já possui turmas")

    now = datetime.now(timezone.utc).isoformat()
    
    # Se não há período de origem, cria um período vazio (registro placeholder)
    if not periodo_origem or periodo_origem.strip() == "":
        # Registrar período na coleção de períodos para que apareça no dropdown
        user_email = current_user.email.valor if hasattr(current_user.email, 'valor') else str(current_user.email)
        await db.periodos_letivos.update_one(
            {"periodo": periodo_destino},
            {"$setOnInsert": {"periodo": periodo_destino, "created_at": now, "created_by": user_email}},
            upsert=True
        )
        return {
            "message": f"Período {periodo_destino} criado (vazio). Adicione turmas manualmente.",
            "periodo_destino": periodo_destino, "turmas_criadas": 0
        }

    turmas = await db.painel_turmas.find({"periodo_letivo": periodo_origem}, {"_id": 0}).to_list(1000)
    if not turmas:
        raise HTTPException(404, f"Nenhuma turma no período {periodo_origem}")

    batch = []
    for t in turmas:
        batch.append({
            "id": str(uuid.uuid4()),
            "codigo_turma": f"{t['codigo_turma']}-{periodo_destino.replace('.', '')}",
            "nome_curso": t["nome_curso"], "turno": t["turno"],
            "vagas_totais": t["vagas_totais"], "vagas_ocupadas": 0,
            "periodo_letivo": periodo_destino, "modalidade": t.get("modalidade", "CHP"),
            "status": "aberto", "created_at": now, "updated_at": now
        })
    if batch:
        await db.painel_turmas.insert_many(batch)

    return {"message": f"{len(batch)} turmas duplicadas para {periodo_destino}",
            "periodo_origem": periodo_origem, "periodo_destino": periodo_destino, "turmas_criadas": len(batch)}
