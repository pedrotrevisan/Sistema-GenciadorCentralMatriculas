"""Router do Módulo de Pendências Documentais"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.models import (
    PendenciaModel, TipoDocumentoModel, HistoricoContatoModel, 
    AlunoModel, PedidoModel
)

from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/pendencias", tags=["Pendências"])


# DTOs para Pendências
class CriarPendenciaDTO(BaseModel):
    aluno_id: str
    pedido_id: str
    documento_codigo: str
    observacoes: Optional[str] = None


class AtualizarPendenciaDTO(BaseModel):
    status: str  # pendente, aguardando_aluno, em_analise, aprovado, rejeitado, reenvio_necessario
    observacoes: Optional[str] = None
    motivo_rejeicao: Optional[str] = None


class RegistrarContatoDTO(BaseModel):
    tipo_contato: str  # telefone, whatsapp, email, presencial
    descricao: str
    resultado: Optional[str] = None  # atendeu, nao_atendeu, retornou, sem_resposta


# Status de Pendências
STATUS_PENDENCIA = {
    "pendente": "Pendente",
    "aguardando_aluno": "Aguardando Aluno",
    "em_analise": "Em Análise",
    "aprovado": "Aprovado",
    "rejeitado": "Rejeitado",
    "reenvio_necessario": "Reenvio Necessário"
}


@router.get("/tipos-documento")
async def listar_tipos_documento(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os tipos de documento disponíveis"""
    result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.ativo == True).order_by(TipoDocumentoModel.codigo)
    )
    tipos = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "codigo": t.codigo,
            "nome": t.nome,
            "obrigatorio": t.obrigatorio,
            "observacoes": t.observacoes
        }
        for t in tipos
    ]


@router.get("/dashboard")
async def dashboard_pendencias(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Dashboard da Central de Pendências"""
    # Contagem por status
    status_query = await session.execute(
        select(PendenciaModel.status, func.count(PendenciaModel.id))
        .group_by(PendenciaModel.status)
    )
    contagem_status = {row[0]: row[1] for row in status_query.fetchall()}
    
    # Contagem por tipo de documento
    tipo_query = await session.execute(
        select(PendenciaModel.documento_codigo, func.count(PendenciaModel.id))
        .group_by(PendenciaModel.documento_codigo)
    )
    por_tipo = [{"tipo": row[0], "total": row[1]} for row in tipo_query.fetchall()]
    
    # Total geral
    total_query = await session.execute(select(func.count(PendenciaModel.id)))
    total = total_query.scalar() or 0
    
    # Total em aberto (não aprovado)
    abertos_query = await session.execute(
        select(func.count(PendenciaModel.id))
        .where(PendenciaModel.status != 'aprovado')
    )
    total_abertos = abertos_query.scalar() or 0
    
    return {
        "contagem_status": contagem_status,
        "por_tipo": por_tipo,
        "total": total,
        "total_abertos": total_abertos,
        "total_pendente": contagem_status.get('pendente', 0),
        "total_aguardando": contagem_status.get('aguardando_aluno', 0),
        "total_em_analise": contagem_status.get('em_analise', 0),
        "total_aprovado": contagem_status.get('aprovado', 0),
        "total_rejeitado": contagem_status.get('rejeitado', 0),
        "total_reenvio": contagem_status.get('reenvio_necessario', 0)
    }


@router.get("")
async def listar_pendencias(
    status: Optional[str] = None,
    documento_codigo: Optional[str] = None,
    aluno_nome: Optional[str] = None,
    pedido_id: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todas as pendências com filtros"""
    # Query base com joins
    query = (
        select(PendenciaModel, AlunoModel.nome.label('aluno_nome'), AlunoModel.cpf.label('aluno_cpf'))
        .join(AlunoModel, PendenciaModel.aluno_id == AlunoModel.id)
    )
    
    # Filtros
    conditions = []
    if status and status != 'todos':
        conditions.append(PendenciaModel.status == status)
    if documento_codigo and documento_codigo != 'todos':
        conditions.append(PendenciaModel.documento_codigo == documento_codigo)
    if aluno_nome:
        conditions.append(AlunoModel.nome.ilike(f'%{aluno_nome}%'))
    if pedido_id:
        conditions.append(PendenciaModel.pedido_id == pedido_id)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Ordenação: mais recentes primeiro
    query = query.order_by(PendenciaModel.created_at.desc())
    
    # Contagem total
    count_query = select(func.count(PendenciaModel.id)).join(AlunoModel, PendenciaModel.aluno_id == AlunoModel.id)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginação
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)
    
    result = await session.execute(query)
    rows = result.all()
    
    # Buscar tipos de documento para labels
    tipos_result = await session.execute(select(TipoDocumentoModel))
    tipos_dict = {t.codigo: t.nome for t in tipos_result.scalars().all()}
    
    pendencias = []
    for row in rows:
        pendencia = row[0]
        aluno_nome_val = row[1]
        aluno_cpf = row[2]
        
        # Contar tentativas de contato
        contatos_result = await session.execute(
            select(func.count(HistoricoContatoModel.id))
            .where(HistoricoContatoModel.pendencia_id == pendencia.id)
        )
        total_contatos = contatos_result.scalar() or 0
        
        pendencias.append({
            "id": pendencia.id,
            "aluno_id": pendencia.aluno_id,
            "aluno_nome": aluno_nome_val,
            "aluno_cpf": aluno_cpf,
            "pedido_id": pendencia.pedido_id,
            "documento_codigo": pendencia.documento_codigo,
            "documento_nome": tipos_dict.get(pendencia.documento_codigo, pendencia.documento_codigo),
            "status": pendencia.status,
            "status_label": STATUS_PENDENCIA.get(pendencia.status, pendencia.status),
            "observacoes": pendencia.observacoes,
            "motivo_rejeicao": pendencia.motivo_rejeicao,
            "total_contatos": total_contatos,
            "criado_por_nome": pendencia.criado_por_nome,
            "created_at": pendencia.created_at.isoformat() if pendencia.created_at else None,
            "updated_at": pendencia.updated_at.isoformat() if pendencia.updated_at else None
        })
    
    return {
        "pendencias": pendencias,
        "paginacao": {
            "pagina_atual": pagina,
            "por_pagina": por_pagina,
            "total_itens": total,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    }


@router.post("")
async def criar_pendencia(
    dto: CriarPendenciaDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria uma nova pendência de documento"""
    # Verificar se aluno existe
    aluno_result = await session.execute(
        select(AlunoModel).where(AlunoModel.id == dto.aluno_id)
    )
    aluno = aluno_result.scalar_one_or_none()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    # Verificar se pedido existe
    pedido_result = await session.execute(
        select(PedidoModel).where(PedidoModel.id == dto.pedido_id)
    )
    pedido = pedido_result.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Verificar se já existe pendência para este documento/aluno
    existente_result = await session.execute(
        select(PendenciaModel).where(
            and_(
                PendenciaModel.aluno_id == dto.aluno_id,
                PendenciaModel.documento_codigo == dto.documento_codigo,
                PendenciaModel.status != 'aprovado'
            )
        )
    )
    if existente_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Já existe uma pendência em aberto para este documento")
    
    pendencia = PendenciaModel(
        id=str(uuid.uuid4()),
        aluno_id=dto.aluno_id,
        pedido_id=dto.pedido_id,
        documento_codigo=dto.documento_codigo,
        status="pendente",
        observacoes=dto.observacoes,
        criado_por_id=usuario.id,
        criado_por_nome=usuario.nome
    )
    
    session.add(pendencia)
    await session.commit()
    
    return {
        "id": pendencia.id,
        "mensagem": "Pendência criada com sucesso",
        "status": pendencia.status
    }


@router.post("/lote")
async def criar_pendencias_lote(
    pendencias: List[CriarPendenciaDTO],
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria múltiplas pendências de uma vez"""
    criadas = []
    erros = []
    
    for idx, dto in enumerate(pendencias):
        try:
            # Verificar se aluno existe
            aluno_result = await session.execute(
                select(AlunoModel).where(AlunoModel.id == dto.aluno_id)
            )
            if not aluno_result.scalar_one_or_none():
                erros.append({"index": idx, "erro": "Aluno não encontrado"})
                continue
            
            # Verificar se já existe
            existente_result = await session.execute(
                select(PendenciaModel).where(
                    and_(
                        PendenciaModel.aluno_id == dto.aluno_id,
                        PendenciaModel.documento_codigo == dto.documento_codigo,
                        PendenciaModel.status != 'aprovado'
                    )
                )
            )
            if existente_result.scalar_one_or_none():
                erros.append({"index": idx, "erro": "Pendência já existe"})
                continue
            
            pendencia = PendenciaModel(
                id=str(uuid.uuid4()),
                aluno_id=dto.aluno_id,
                pedido_id=dto.pedido_id,
                documento_codigo=dto.documento_codigo,
                status="pendente",
                observacoes=dto.observacoes,
                criado_por_id=usuario.id,
                criado_por_nome=usuario.nome
            )
            session.add(pendencia)
            criadas.append(pendencia.id)
            
        except Exception as e:
            erros.append({"index": idx, "erro": str(e)})
    
    await session.commit()
    
    return {
        "criadas": len(criadas),
        "erros": len(erros),
        "detalhes_erros": erros
    }


@router.get("/{pendencia_id}")
async def buscar_pendencia(
    pendencia_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Busca detalhes de uma pendência específica"""
    result = await session.execute(
        select(PendenciaModel, AlunoModel)
        .join(AlunoModel, PendenciaModel.aluno_id == AlunoModel.id)
        .where(PendenciaModel.id == pendencia_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    pendencia, aluno = row
    
    # Buscar histórico de contatos
    contatos_result = await session.execute(
        select(HistoricoContatoModel)
        .where(HistoricoContatoModel.pendencia_id == pendencia_id)
        .order_by(HistoricoContatoModel.created_at.desc())
    )
    contatos = contatos_result.scalars().all()
    
    # Buscar nome do tipo de documento
    tipo_result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.codigo == pendencia.documento_codigo)
    )
    tipo = tipo_result.scalar_one_or_none()
    
    return {
        "id": pendencia.id,
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "cpf": aluno.cpf,
            "email": aluno.email,
            "telefone": aluno.telefone
        },
        "pedido_id": pendencia.pedido_id,
        "documento_codigo": pendencia.documento_codigo,
        "documento_nome": tipo.nome if tipo else pendencia.documento_codigo,
        "status": pendencia.status,
        "status_label": STATUS_PENDENCIA.get(pendencia.status, pendencia.status),
        "observacoes": pendencia.observacoes,
        "motivo_rejeicao": pendencia.motivo_rejeicao,
        "historico_contatos": [
            {
                "id": c.id,
                "tipo_contato": c.tipo_contato,
                "descricao": c.descricao,
                "resultado": c.resultado,
                "responsavel_nome": c.responsavel_nome,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in contatos
        ],
        "criado_por_nome": pendencia.criado_por_nome,
        "atualizado_por_nome": pendencia.atualizado_por_nome,
        "created_at": pendencia.created_at.isoformat() if pendencia.created_at else None,
        "updated_at": pendencia.updated_at.isoformat() if pendencia.updated_at else None
    }


@router.put("/{pendencia_id}")
async def atualizar_pendencia(
    pendencia_id: str,
    dto: AtualizarPendenciaDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza o status de uma pendência"""
    result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    # Validar status
    if dto.status not in STATUS_PENDENCIA:
        raise HTTPException(status_code=400, detail=f"Status inválido. Opções: {', '.join(STATUS_PENDENCIA.keys())}")
    
    pendencia.status = dto.status
    if dto.observacoes is not None:
        pendencia.observacoes = dto.observacoes
    if dto.motivo_rejeicao is not None:
        pendencia.motivo_rejeicao = dto.motivo_rejeicao
    
    pendencia.atualizado_por_id = usuario.id
    pendencia.atualizado_por_nome = usuario.nome
    pendencia.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    return {
        "id": pendencia.id,
        "mensagem": "Pendência atualizada com sucesso",
        "status": pendencia.status
    }


@router.post("/{pendencia_id}/contatos")
async def registrar_contato(
    pendencia_id: str,
    dto: RegistrarContatoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Registra uma tentativa de contato com o aluno"""
    # Verificar se pendência existe
    pendencia_result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = pendencia_result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    contato = HistoricoContatoModel(
        id=str(uuid.uuid4()),
        pendencia_id=pendencia_id,
        tipo_contato=dto.tipo_contato,
        descricao=dto.descricao,
        resultado=dto.resultado,
        responsavel_id=usuario.id,
        responsavel_nome=usuario.nome
    )
    
    session.add(contato)
    
    # Atualizar status da pendência se necessário
    if dto.resultado and pendencia.status == 'pendente':
        pendencia.status = 'aguardando_aluno'
        pendencia.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    return {
        "id": contato.id,
        "mensagem": "Contato registrado com sucesso",
        "pendencia_status": pendencia.status
    }


@router.get("/aluno/{aluno_id}")
async def listar_pendencias_aluno(
    aluno_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todas as pendências de um aluno específico"""
    result = await session.execute(
        select(PendenciaModel)
        .where(PendenciaModel.aluno_id == aluno_id)
        .order_by(PendenciaModel.created_at.desc())
    )
    pendencias = result.scalars().all()
    
    # Buscar tipos de documento
    tipos_result = await session.execute(select(TipoDocumentoModel))
    tipos_dict = {t.codigo: t.nome for t in tipos_result.scalars().all()}
    
    return [
        {
            "id": p.id,
            "documento_codigo": p.documento_codigo,
            "documento_nome": tipos_dict.get(p.documento_codigo, p.documento_codigo),
            "status": p.status,
            "status_label": STATUS_PENDENCIA.get(p.status, p.status),
            "observacoes": p.observacoes,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in pendencias
    ]


@router.delete("/{pendencia_id}")
async def deletar_pendencia(
    pendencia_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Deleta uma pendência (apenas admin)"""
    if usuario.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir pendências")
    
    result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    await session.delete(pendencia)
    await session.commit()
    
    return {"mensagem": "Pendência excluída com sucesso"}
