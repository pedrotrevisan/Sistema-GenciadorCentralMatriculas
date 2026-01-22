"""Router de Cadastros (Cursos, Projetos, Empresas)"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.infrastructure.persistence.models import CursoModel, ProjetoModel, EmpresaModel
from src.domain.value_objects import StatusPedido

from .dependencies import get_db_session, require_permission

router = APIRouter(tags=["Cadastros"])


# ==================== CURSOS ====================

class CursoRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = None


class CursoResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True


@router.get("/cursos", tags=["Cursos"])
async def listar_cursos(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os cursos"""
    query = select(CursoModel)
    if ativo is not None:
        query = query.where(CursoModel.ativo == ativo)
    query = query.order_by(CursoModel.nome)
    result = await session.execute(query)
    cursos = result.scalars().all()
    return [{"id": c.id, "nome": c.nome, "descricao": c.descricao, "ativo": c.ativo} for c in cursos]


@router.post("/cursos", response_model=CursoResponse, status_code=201, tags=["Cursos"])
async def criar_curso(
    request: CursoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria um novo curso (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(CursoModel).where(CursoModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Curso já existe")
    
    curso = CursoModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        descricao=request.descricao
    )
    session.add(curso)
    await session.commit()
    return {"id": curso.id, "nome": curso.nome, "descricao": curso.descricao, "ativo": curso.ativo}


@router.put("/cursos/{curso_id}", response_model=CursoResponse, tags=["Cursos"])
async def atualizar_curso(
    curso_id: str,
    request: CursoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza um curso (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = result.scalar_one_or_none()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    curso.nome = request.nome
    curso.descricao = request.descricao
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": curso.id, "nome": curso.nome, "descricao": curso.descricao, "ativo": curso.ativo}


@router.delete("/cursos/{curso_id}", tags=["Cursos"])
async def deletar_curso(
    curso_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa um curso (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = result.scalar_one_or_none()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    curso.ativo = False
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Curso desativado com sucesso"}


# ==================== PROJETOS ====================

class ProjetoRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = None


class ProjetoResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True


@router.get("/projetos", tags=["Projetos"])
async def listar_projetos(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os projetos"""
    query = select(ProjetoModel)
    if ativo is not None:
        query = query.where(ProjetoModel.ativo == ativo)
    query = query.order_by(ProjetoModel.nome)
    result = await session.execute(query)
    projetos = result.scalars().all()
    return [{"id": p.id, "nome": p.nome, "descricao": p.descricao, "ativo": p.ativo} for p in projetos]


@router.post("/projetos", response_model=ProjetoResponse, status_code=201, tags=["Projetos"])
async def criar_projeto(
    request: ProjetoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria um novo projeto (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Projeto já existe")
    
    projeto = ProjetoModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        descricao=request.descricao
    )
    session.add(projeto)
    await session.commit()
    return {"id": projeto.id, "nome": projeto.nome, "descricao": projeto.descricao, "ativo": projeto.ativo}


@router.put("/projetos/{projeto_id}", response_model=ProjetoResponse, tags=["Projetos"])
async def atualizar_projeto(
    projeto_id: str,
    request: ProjetoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza um projeto (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.id == projeto_id))
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    projeto.nome = request.nome
    projeto.descricao = request.descricao
    projeto.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": projeto.id, "nome": projeto.nome, "descricao": projeto.descricao, "ativo": projeto.ativo}


@router.delete("/projetos/{projeto_id}", tags=["Projetos"])
async def deletar_projeto(
    projeto_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa um projeto (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.id == projeto_id))
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    projeto.ativo = False
    projeto.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Projeto desativado com sucesso"}


# ==================== EMPRESAS ====================

class EmpresaRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    cnpj: Optional[str] = None


class EmpresaResponse(BaseModel):
    id: str
    nome: str
    cnpj: Optional[str] = None
    ativo: bool = True


@router.get("/empresas", tags=["Empresas"])
async def listar_empresas(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todas as empresas"""
    query = select(EmpresaModel)
    if ativo is not None:
        query = query.where(EmpresaModel.ativo == ativo)
    query = query.order_by(EmpresaModel.nome)
    result = await session.execute(query)
    empresas = result.scalars().all()
    return [{"id": e.id, "nome": e.nome, "cnpj": e.cnpj, "ativo": e.ativo} for e in empresas]


@router.post("/empresas", response_model=EmpresaResponse, status_code=201, tags=["Empresas"])
async def criar_empresa(
    request: EmpresaRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria uma nova empresa (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Empresa já existe")
    
    empresa = EmpresaModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        cnpj=request.cnpj
    )
    session.add(empresa)
    await session.commit()
    return {"id": empresa.id, "nome": empresa.nome, "cnpj": empresa.cnpj, "ativo": empresa.ativo}


@router.put("/empresas/{empresa_id}", response_model=EmpresaResponse, tags=["Empresas"])
async def atualizar_empresa(
    empresa_id: str,
    request: EmpresaRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza uma empresa (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.nome = request.nome
    empresa.cnpj = request.cnpj
    empresa.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": empresa.id, "nome": empresa.nome, "cnpj": empresa.cnpj, "ativo": empresa.ativo}


@router.delete("/empresas/{empresa_id}", tags=["Empresas"])
async def deletar_empresa(
    empresa_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa uma empresa (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.ativo = False
    empresa.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Empresa desativada com sucesso"}


# ==================== DADOS AUXILIARES ====================

@router.get("/status-pedido", tags=["Auxiliares"])
async def listar_status():
    """Lista status disponíveis"""
    return [
        {"value": s.value, "label": s.label}
        for s in StatusPedido
    ]
