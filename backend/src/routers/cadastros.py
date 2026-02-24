"""Router de Cadastros (Cursos, Projetos, Empresas)"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import io

from src.infrastructure.persistence.models import CursoModel, ProjetoModel, EmpresaModel
from src.domain.value_objects import StatusPedido

from .dependencies import get_db_session, require_permission

router = APIRouter(tags=["Cadastros"])


# ==================== TIPOS E OPÇÕES ====================

TIPOS_CURSO = [
    {"value": "tecnico", "label": "Escola Técnica"},
    {"value": "graduacao", "label": "Graduação"},
    {"value": "pos_graduacao", "label": "Pós-Graduação"},
    {"value": "livre", "label": "Curso Livre"},
    {"value": "capacitacao", "label": "Capacitação"},
]

MODALIDADES_CURSO = [
    {"value": "presencial", "label": "Presencial"},
    {"value": "ead", "label": "EAD"},
    {"value": "hibrido", "label": "Híbrido"},
]

AREAS_CURSO = [
    {"value": "tecnologia", "label": "Tecnologia da Informação"},
    {"value": "industria", "label": "Indústria e Manufatura"},
    {"value": "gestao", "label": "Gestão e Negócios"},
    {"value": "saude", "label": "Saúde"},
    {"value": "automacao", "label": "Automação e Mecatrônica"},
    {"value": "eletrica", "label": "Elétrica e Eletrônica"},
    {"value": "mecanica", "label": "Mecânica"},
    {"value": "quimica", "label": "Química"},
    {"value": "seguranca", "label": "Segurança do Trabalho"},
    {"value": "outros", "label": "Outros"},
]


# ==================== CURSOS ====================

class CursoRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = None
    tipo: Optional[str] = None  # tecnico, graduacao, pos_graduacao, livre
    modalidade: Optional[str] = None  # presencial, ead, hibrido
    area: Optional[str] = None
    carga_horaria: Optional[str] = None
    duracao: Optional[str] = None


class CursoResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    tipo: Optional[str] = None
    tipo_label: Optional[str] = None
    modalidade: Optional[str] = None
    modalidade_label: Optional[str] = None
    area: Optional[str] = None
    area_label: Optional[str] = None
    carga_horaria: Optional[str] = None
    duracao: Optional[str] = None
    ativo: bool = True


def get_label(lista: List[dict], value: str) -> Optional[str]:
    """Retorna o label de um valor em uma lista de opções"""
    if not value:
        return None
    for item in lista:
        if item["value"] == value:
            return item["label"]
    return value


@router.get("/cursos/opcoes", tags=["Cursos"])
async def listar_opcoes_cursos():
    """Lista todas as opções disponíveis para cursos"""
    return {
        "tipos": TIPOS_CURSO,
        "modalidades": MODALIDADES_CURSO,
        "areas": AREAS_CURSO
    }


@router.get("/cursos", tags=["Cursos"])
async def listar_cursos(
    ativo: Optional[bool] = None,
    tipo: Optional[str] = None,
    modalidade: Optional[str] = None,
    area: Optional[str] = None,
    busca: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os cursos com filtros"""
    query = select(CursoModel)
    
    # Filtros
    if ativo is not None:
        query = query.where(CursoModel.ativo == ativo)
    if tipo:
        query = query.where(CursoModel.tipo == tipo)
    if modalidade:
        query = query.where(CursoModel.modalidade == modalidade)
    if area:
        query = query.where(CursoModel.area == area)
    if busca:
        query = query.where(
            or_(
                CursoModel.nome.ilike(f'%{busca}%'),
                CursoModel.descricao.ilike(f'%{busca}%')
            )
        )
    
    query = query.order_by(CursoModel.tipo, CursoModel.nome)
    result = await session.execute(query)
    cursos = result.scalars().all()
    
    return [
        {
            "id": c.id, 
            "nome": c.nome, 
            "descricao": c.descricao, 
            "tipo": c.tipo,
            "tipo_label": get_label(TIPOS_CURSO, c.tipo),
            "modalidade": c.modalidade,
            "modalidade_label": get_label(MODALIDADES_CURSO, c.modalidade),
            "area": c.area,
            "area_label": get_label(AREAS_CURSO, c.area),
            "carga_horaria": c.carga_horaria,
            "duracao": c.duracao,
            "ativo": c.ativo
        } 
        for c in cursos
    ]


@router.get("/cursos/estatisticas", tags=["Cursos"])
async def estatisticas_cursos(
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna estatísticas dos cursos cadastrados"""
    from sqlalchemy import func
    
    # Total por tipo
    tipo_query = await session.execute(
        select(CursoModel.tipo, func.count(CursoModel.id))
        .where(CursoModel.ativo == True)
        .group_by(CursoModel.tipo)
    )
    por_tipo = {row[0] or "sem_tipo": row[1] for row in tipo_query.fetchall()}
    
    # Total por modalidade
    modalidade_query = await session.execute(
        select(CursoModel.modalidade, func.count(CursoModel.id))
        .where(CursoModel.ativo == True)
        .group_by(CursoModel.modalidade)
    )
    por_modalidade = {row[0] or "sem_modalidade": row[1] for row in modalidade_query.fetchall()}
    
    # Total geral
    total_query = await session.execute(
        select(func.count(CursoModel.id)).where(CursoModel.ativo == True)
    )
    total = total_query.scalar() or 0
    
    return {
        "total": total,
        "por_tipo": por_tipo,
        "por_modalidade": por_modalidade
    }


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
        descricao=request.descricao,
        tipo=request.tipo,
        modalidade=request.modalidade,
        area=request.area,
        carga_horaria=request.carga_horaria,
        duracao=request.duracao
    )
    session.add(curso)
    await session.commit()
    
    return {
        "id": curso.id, 
        "nome": curso.nome, 
        "descricao": curso.descricao,
        "tipo": curso.tipo,
        "tipo_label": get_label(TIPOS_CURSO, curso.tipo),
        "modalidade": curso.modalidade,
        "modalidade_label": get_label(MODALIDADES_CURSO, curso.modalidade),
        "area": curso.area,
        "area_label": get_label(AREAS_CURSO, curso.area),
        "carga_horaria": curso.carga_horaria,
        "duracao": curso.duracao,
        "ativo": curso.ativo
    }


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
    curso.tipo = request.tipo
    curso.modalidade = request.modalidade
    curso.area = request.area
    curso.carga_horaria = request.carga_horaria
    curso.duracao = request.duracao
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    
    return {
        "id": curso.id, 
        "nome": curso.nome, 
        "descricao": curso.descricao,
        "tipo": curso.tipo,
        "tipo_label": get_label(TIPOS_CURSO, curso.tipo),
        "modalidade": curso.modalidade,
        "modalidade_label": get_label(MODALIDADES_CURSO, curso.modalidade),
        "area": curso.area,
        "area_label": get_label(AREAS_CURSO, curso.area),
        "carga_horaria": curso.carga_horaria,
        "duracao": curso.duracao,
        "ativo": curso.ativo
    }


@router.patch("/cursos/{curso_id}/ativar", tags=["Cursos"])
async def ativar_curso(
    curso_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Ativa um curso desativado (Admin)"""
    usuario, session = deps
    
    result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = result.scalar_one_or_none()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    curso.ativo = True
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Curso ativado com sucesso"}


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
