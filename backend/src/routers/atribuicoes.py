"""Router de Sistema de Atribuições/Chamados"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.domain.entities import Usuario
from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/atribuicoes", tags=["Atribuições"])


# ==================== DTOs ====================

class AtribuirRequest(BaseModel):
    tipo: str  # pedido, pendencia, reembolso
    item_id: str
    responsavel_id: str
    prioridade: Optional[str] = "normal"  # baixa, normal, alta, urgente
    observacao: Optional[str] = None


class NotificacaoRequest(BaseModel):
    destinatario_id: str
    titulo: str
    mensagem: str
    tipo: str = "info"  # info, alerta, urgente
    link: Optional[str] = None


# ==================== MINHA CAIXA DE ENTRADA ====================

@router.get("/minha-caixa")
async def minha_caixa_entrada(
    status: Optional[str] = None,  # pendente, em_andamento, concluido
    tipo: Optional[str] = None,  # pedido, pendencia, reembolso
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna todas as demandas atribuídas ao usuário logado"""
    from src.infrastructure.persistence.models import PedidoModel, PendenciaModel, ReembolsoModel
    
    items = []
    
    # Buscar pedidos atribuídos
    if not tipo or tipo == "pedido":
        result = await session.execute(
            select(PedidoModel)
            .where(PedidoModel.responsavel_id == usuario.id)
            .order_by(desc(PedidoModel.updated_at))
        )
        pedidos = result.scalars().all()
        for p in pedidos:
            items.append({
                "id": p.id,
                "tipo": "pedido",
                "titulo": f"Matrícula - {p.numero_protocolo or 'S/N'}",
                "descricao": f"{p.curso_nome}",
                "status": p.status,
                "prioridade": getattr(p, 'prioridade', 'normal'),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "link": f"/pedidos/{p.id}"
            })
    
    # Buscar pendências atribuídas
    if not tipo or tipo == "pendencia":
        result = await session.execute(
            select(PendenciaModel)
            .where(PendenciaModel.responsavel_id == usuario.id)
            .order_by(desc(PendenciaModel.updated_at))
        )
        pendencias = result.scalars().all()
        for pend in pendencias:
            items.append({
                "id": pend.id,
                "tipo": "pendencia",
                "titulo": f"Pendência - {pend.documento_nome or pend.documento_codigo}",
                "descricao": pend.observacoes or "Documento pendente",
                "status": pend.status,
                "prioridade": getattr(pend, 'prioridade', 'normal'),
                "created_at": pend.created_at.isoformat() if pend.created_at else None,
                "updated_at": pend.updated_at.isoformat() if pend.updated_at else None,
                "link": f"/pendencias?id={pend.id}"
            })
    
    # Buscar reembolsos atribuídos
    if not tipo or tipo == "reembolso":
        result = await session.execute(
            select(ReembolsoModel)
            .where(ReembolsoModel.responsavel_id == usuario.id)
            .order_by(desc(ReembolsoModel.updated_at))
        )
        reembolsos = result.scalars().all()
        for r in reembolsos:
            items.append({
                "id": r.id,
                "tipo": "reembolso",
                "titulo": f"Reembolso - {r.aluno_nome}",
                "descricao": f"{r.curso} - {r.motivo}",
                "status": r.status,
                "prioridade": getattr(r, 'prioridade', 'normal'),
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "link": f"/reembolsos?id={r.id}"
            })
    
    # Filtrar por status se especificado
    if status:
        status_map = {
            "pendente": ["pendente", "aberto", "aguardando_aluno", "aguardando_dados_bancarios"],
            "em_andamento": ["em_analise", "documentacao_pendente", "enviado_financeiro"],
            "concluido": ["aprovado", "realizado", "exportado", "pago", "cancelado", "rejeitado"]
        }
        allowed_status = status_map.get(status, [])
        items = [i for i in items if i["status"] in allowed_status]
    
    # Ordenar por prioridade e data
    prioridade_ordem = {"urgente": 0, "alta": 1, "normal": 2, "baixa": 3}
    items.sort(key=lambda x: (prioridade_ordem.get(x.get("prioridade", "normal"), 2), x.get("updated_at", "") or ""))
    
    return {
        "total": len(items),
        "items": items
    }


@router.get("/resumo")
async def resumo_atribuicoes(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna resumo das atribuições do usuário"""
    from src.infrastructure.persistence.models import PedidoModel, PendenciaModel, ReembolsoModel
    
    # Contar pedidos
    result = await session.execute(
        select(func.count(PedidoModel.id))
        .where(PedidoModel.responsavel_id == usuario.id)
    )
    total_pedidos = result.scalar() or 0
    
    # Contar pendências
    result = await session.execute(
        select(func.count(PendenciaModel.id))
        .where(PendenciaModel.responsavel_id == usuario.id)
    )
    total_pendencias = result.scalar() or 0
    
    # Contar reembolsos
    result = await session.execute(
        select(func.count(ReembolsoModel.id))
        .where(ReembolsoModel.responsavel_id == usuario.id)
    )
    total_reembolsos = result.scalar() or 0
    
    return {
        "total": total_pedidos + total_pendencias + total_reembolsos,
        "pedidos": total_pedidos,
        "pendencias": total_pendencias,
        "reembolsos": total_reembolsos
    }


# ==================== ATRIBUIÇÃO ====================

@router.post("/atribuir")
async def atribuir_demanda(
    request: AtribuirRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atribui uma demanda a um responsável e envia notificação por email"""
    from src.infrastructure.persistence.models import PedidoModel, PendenciaModel, ReembolsoModel, UsuarioModel
    from src.services.email_service import email_service
    import os
    
    # Verificar se responsável existe
    result = await session.execute(
        select(UsuarioModel).where(UsuarioModel.id == request.responsavel_id)
    )
    responsavel = result.scalar_one_or_none()
    if not responsavel:
        raise HTTPException(404, "Responsável não encontrado")
    
    titulo_demanda = ""
    descricao_demanda = ""
    link_demanda = ""
    
    # Atribuir baseado no tipo
    if request.tipo == "pedido":
        result = await session.execute(
            select(PedidoModel).where(PedidoModel.id == request.item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(404, "Pedido não encontrado")
        item.responsavel_id = request.responsavel_id
        item.responsavel_nome = responsavel.nome
        if request.prioridade:
            item.prioridade = request.prioridade
        titulo_demanda = f"Matrícula - {item.numero_protocolo or 'S/N'}"
        descricao_demanda = item.curso_nome or ""
        link_demanda = f"/pedidos/{item.id}"
        
    elif request.tipo == "pendencia":
        result = await session.execute(
            select(PendenciaModel).where(PendenciaModel.id == request.item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(404, "Pendência não encontrada")
        item.responsavel_id = request.responsavel_id
        item.responsavel_nome = responsavel.nome
        if request.prioridade:
            item.prioridade = request.prioridade
        titulo_demanda = f"Pendência - {item.documento_nome or item.documento_codigo}"
        descricao_demanda = item.observacoes or "Documento pendente"
        link_demanda = f"/pendencias?id={item.id}"
        
    elif request.tipo == "reembolso":
        result = await session.execute(
            select(ReembolsoModel).where(ReembolsoModel.id == request.item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(404, "Reembolso não encontrado")
        item.responsavel_id = request.responsavel_id
        item.responsavel_nome = responsavel.nome
        if request.prioridade:
            item.prioridade = request.prioridade
        titulo_demanda = f"Reembolso - {item.aluno_nome}"
        descricao_demanda = f"{item.curso} - {item.motivo}"
        link_demanda = f"/reembolsos?id={item.id}"
    else:
        raise HTTPException(400, "Tipo inválido. Use: pedido, pendencia ou reembolso")
    
    await session.commit()
    
    # Enviar notificação por email (em background, não bloqueia a resposta)
    base_url = os.environ.get('FRONTEND_URL', 'https://operacional-hub.preview.emergentagent.com')
    full_link = f"{base_url}{link_demanda}"
    
    # Tentar enviar email (não falha se não conseguir)
    try:
        email_service.send_atribuicao_notification(
            to_email=responsavel.email,
            to_name=responsavel.nome,
            tipo_demanda=request.tipo,
            titulo_demanda=titulo_demanda,
            descricao=descricao_demanda,
            prioridade=request.prioridade or "normal",
            link=full_link,
            atribuido_por=usuario.nome
        )
    except Exception as e:
        # Log do erro mas não falha a requisição
        import logging
        logging.warning(f"Falha ao enviar email de notificação: {e}")
    
    return {
        "message": f"Demanda atribuída a {responsavel.nome}",
        "responsavel": {
            "id": responsavel.id,
            "nome": responsavel.nome,
            "email": responsavel.email
        },
        "notificacao_email": email_service.enabled
    }


@router.delete("/atribuir/{tipo}/{item_id}")
async def remover_atribuicao(
    tipo: str,
    item_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Remove atribuição de uma demanda"""
    from src.infrastructure.persistence.models import PedidoModel, PendenciaModel, ReembolsoModel
    
    if tipo == "pedido":
        result = await session.execute(
            select(PedidoModel).where(PedidoModel.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.responsavel_id = None
            item.responsavel_nome = None
    elif tipo == "pendencia":
        result = await session.execute(
            select(PendenciaModel).where(PendenciaModel.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.responsavel_id = None
            item.responsavel_nome = None
    elif tipo == "reembolso":
        result = await session.execute(
            select(ReembolsoModel).where(ReembolsoModel.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.responsavel_id = None
            item.responsavel_nome = None
    else:
        raise HTTPException(400, "Tipo inválido")
    
    await session.commit()
    return {"message": "Atribuição removida"}


# ==================== LISTAR RESPONSÁVEIS ====================

@router.get("/responsaveis")
async def listar_responsaveis(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista usuários que podem ser responsáveis por demandas"""
    from src.infrastructure.persistence.models import UsuarioModel
    
    result = await session.execute(
        select(UsuarioModel)
        .where(UsuarioModel.ativo == True)
        .where(UsuarioModel.role.in_(['assistente', 'admin']))
        .order_by(UsuarioModel.nome)
    )
    usuarios = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "role": u.role
        }
        for u in usuarios
    ]
