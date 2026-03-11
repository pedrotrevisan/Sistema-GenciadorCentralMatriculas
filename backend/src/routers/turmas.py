"""Router de Turmas - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/turmas", tags=["Gestão de Turmas"])

class CriarTurmaDTO(BaseModel):
    curso_id: str
    nome: str
    turno: str
    vagas: int
    periodo: Optional[str] = "2026.1"

class ReservarVagaDTO(BaseModel):
    turma_id: str
    pedido_id: str
    aluno_nome: str

@router.get("")
async def listar_turmas(curso_id: Optional[str] = None, usuario: Usuario = Depends(get_current_user)):
    query = {}
    if curso_id:
        query["curso_id"] = curso_id
    turmas = await db.turmas.find(query, {"_id": 0}).sort("nome", 1).to_list(500)
    return {"turmas": turmas, "total": len(turmas)}

@router.post("", status_code=201)
async def criar_turma(dto: CriarTurmaDTO, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin", "assistente"):
        raise HTTPException(403, "Sem permissão")
    doc = {
        "id": str(uuid.uuid4()), "curso_id": dto.curso_id, "nome": dto.nome,
        "turno": dto.turno, "vagas_totais": dto.vagas, "vagas_ocupadas": 0,
        "periodo": dto.periodo, "ativa": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.turmas.insert_one(doc)
    return doc

@router.get("/{turma_id}")
async def buscar_turma(turma_id: str, usuario: Usuario = Depends(get_current_user)):
    t = await db.turmas.find_one({"id": turma_id}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    reservas = await db.reservas_vaga.find({"turma_id": turma_id}, {"_id": 0}).to_list(100)
    t["reservas"] = reservas
    return t

@router.post("/{turma_id}/reservar")
async def reservar_vaga(turma_id: str, dto: ReservarVagaDTO, usuario: Usuario = Depends(get_current_user)):
    t = await db.turmas.find_one({"id": turma_id})
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    vagas = t.get("vagas_totais", 0)
    ocupadas = t.get("vagas_ocupadas", 0)
    if ocupadas >= vagas:
        raise HTTPException(409, "Turma lotada")
    reserva = {
        "id": str(uuid.uuid4()), "turma_id": turma_id, "pedido_id": dto.pedido_id,
        "aluno_nome": dto.aluno_nome, "status": "ativa",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reservas_vaga.insert_one(reserva)
    await db.turmas.update_one({"id": turma_id}, {"$inc": {"vagas_ocupadas": 1}})
    return reserva

@router.post("/{turma_id}/liberar/{reserva_id}")
async def liberar_vaga(turma_id: str, reserva_id: str, usuario: Usuario = Depends(get_current_user)):
    result = await db.reservas_vaga.update_one({"id": reserva_id, "turma_id": turma_id}, {"$set": {"status": "cancelada"}})
    if result.matched_count == 0:
        raise HTTPException(404, "Reserva não encontrada")
    await db.turmas.update_one({"id": turma_id}, {"$inc": {"vagas_ocupadas": -1}})
    return {"message": "Vaga liberada"}

@router.get("/{turma_id}/vagas")
async def consultar_vagas(turma_id: str, usuario: Usuario = Depends(get_current_user)):
    t = await db.turmas.find_one({"id": turma_id}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    vagas = t.get("vagas_totais", 0)
    ocupadas = t.get("vagas_ocupadas", 0)
    return {"turma_id": turma_id, "vagas_totais": vagas, "vagas_ocupadas": ocupadas,
            "vagas_disponiveis": vagas - ocupadas, "percentual": round((ocupadas/vagas*100) if vagas>0 else 0, 1)}
