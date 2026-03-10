"""
Router de Pedidos Refatorado
Contém todas as rotas de CRUD de pedidos, dashboard, analytics e timeline
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from src.domain.entities import Usuario
from src.domain.value_objects import StatusPedido
from src.infrastructure.persistence.repositories import PedidoRepository, UsuarioRepository, AuditoriaRepository
from src.infrastructure.persistence.models import PedidoModel, AlunoModel, AuditoriaModel
from src.application.dtos.request import CriarPedidoDTO, AtualizarStatusDTO, FiltrosPedidoDTO
from src.application.dtos.response import PedidoResponseDTO, ListaPedidosResponseDTO
from src.application.use_cases import (
    CriarPedidoMatriculaUseCase, AtualizarStatusPedidoUseCase,
    GerarExportacaoTOTVSUseCase, ConsultarPedidosUseCase
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ==================== DEPENDENCY INJECTION ====================

async def get_db_session():
    """Get database session"""
    from src.infrastructure.persistence.database import async_session
    async with async_session() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> Usuario:
    """Dependency para obter usuário autenticado"""
    from src.infrastructure.security import JWTAuthenticator
    from src.domain.exceptions import AuthenticationException
    
    jwt_auth = JWTAuthenticator()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt_auth.verificar_token(token)
        usuario_id = payload.get("sub")
        
        usuario_repo = UsuarioRepository(session)
        usuario = await usuario_repo.buscar_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        return usuario
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message)
        )


def require_permission(permission: str):
    """Dependency factory para verificar permissão"""
    async def check_permission(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db_session)
    ):
        user = await get_current_user(token, session)
        if not user.tem_permissao(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission}' necessária"
            )
        return user, session
    return check_permission


# ==================== PEDIDOS ROUTES ====================

@router.post("", response_model=dict)
async def criar_pedido(
    request: CriarPedidoDTO,
    deps: tuple = Depends(require_permission("pedido:criar"))
):
    """
    Cria um novo pedido de matrícula COM reserva automática de vaga
    
    Se turma_id for fornecido, reserva vaga automaticamente.
    Retorna informações do pedido E da reserva.
    """
    usuario, session = deps
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    # Se turma_id fornecido, usar use case com reserva
    if request.turma_id:
        from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository
        from src.application.use_cases.criar_pedido_com_reserva_use_case import CriarPedidoComReservaUseCase
        
        turma_repo = TurmaRepository(session)
        reserva_repo = ReservaVagaRepository(session)
        
        criar_pedido_uc = CriarPedidoComReservaUseCase(
            pedido_repo, auditoria_repo, turma_repo, reserva_repo
        )
        
        resultado = await criar_pedido_uc.executar(request, usuario, request.turma_id)
        
        return {
            "pedido": PedidoResponseDTO(**resultado["pedido"].to_dict()).model_dump(),
            "reserva": {
                "id": resultado["reserva"].id if resultado["reserva"] else None,
                "turma_id": resultado["reserva"].turma_id if resultado["reserva"] else None,
                "status": resultado["reserva"].status.value if resultado["reserva"] else None,
                "data_expiracao": resultado["reserva"].data_expiracao.isoformat() if resultado["reserva"] and resultado["reserva"].data_expiracao else None
            } if resultado["reserva"] else None,
            "mensagem_reserva": resultado["mensagem_reserva"]
        }
    
    # Sem turma, usar use case padrão
    criar_pedido_uc = CriarPedidoMatriculaUseCase(pedido_repo, auditoria_repo)
    pedido = await criar_pedido_uc.executar(request, usuario)
    
    return {
        "pedido": PedidoResponseDTO(**pedido.to_dict()).model_dump(),
        "reserva": None,
        "mensagem_reserva": None
    }


@router.get("", response_model=ListaPedidosResponseDTO)
async def listar_pedidos(
    status_filter: Optional[str] = Query(None, alias="status"),
    consultor_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Lista pedidos com filtros"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    
    filtros = FiltrosPedidoDTO(
        status=status_filter,
        consultor_id=consultor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina
    )
    return await consultar_pedidos_uc.listar(filtros, usuario)


@router.get("/dashboard")
async def get_dashboard(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados do dashboard"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    contagem = await consultar_pedidos_uc.contar_por_status(usuario)
    
    # Busca pedidos recentes
    filtros = FiltrosPedidoDTO(pagina=1, por_pagina=5)
    resultado = await consultar_pedidos_uc.listar(filtros, usuario)
    
    return {
        "contagem_status": contagem,
        "pedidos_recentes": [p.model_dump() for p in resultado.pedidos]
    }


@router.get("/analytics")
async def get_analytics(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados analíticos avançados para o Dashboard 2.0"""
    usuario = await get_current_user(token, session)
    
    # 1. Funil de Matrículas - Contagem por status em ordem do fluxo
    funil_query = select(
        PedidoModel.status,
        func.count(PedidoModel.id).label('total')
    ).group_by(PedidoModel.status)
    
    # Filtrar por consultor se não for admin/assistente
    if usuario.role.value == 'consultor':
        funil_query = funil_query.where(PedidoModel.consultor_id == usuario.id)
    
    funil_result = await session.execute(funil_query)
    funil_data = {row.status: row.total for row in funil_result}
    
    # Ordenar funil na sequência lógica
    funil_ordem = ['pendente', 'em_analise', 'documentacao_pendente', 'aprovado', 'realizado', 'exportado']
    funil = [
        {"status": s, "label": s.replace('_', ' ').title(), "total": funil_data.get(s, 0)}
        for s in funil_ordem
    ]
    
    # 2. Tempo Médio de Matrícula (em dias)
    tempo_query = select(
        func.avg(
            func.julianday(PedidoModel.updated_at) - func.julianday(PedidoModel.created_at)
        ).label('tempo_medio')
    ).where(PedidoModel.status.in_(['realizado', 'exportado']))
    
    if usuario.role.value == 'consultor':
        tempo_query = tempo_query.where(PedidoModel.consultor_id == usuario.id)
    
    tempo_result = await session.execute(tempo_query)
    tempo_medio = tempo_result.scalar() or 0
    
    # 3. Top 5 Empresas
    empresas_query = select(
        PedidoModel.empresa_nome,
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.empresa_nome.isnot(None)
    ).group_by(PedidoModel.empresa_nome).order_by(
        func.count(PedidoModel.id).desc()
    ).limit(5)
    
    if usuario.role.value == 'consultor':
        empresas_query = empresas_query.where(PedidoModel.consultor_id == usuario.id)
    
    empresas_result = await session.execute(empresas_query)
    top_empresas = [{"nome": row.empresa_nome or "Sem empresa", "total": row.total} for row in empresas_result]
    
    # 4. Top 5 Projetos
    projetos_query = select(
        PedidoModel.projeto_nome,
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.projeto_nome.isnot(None)
    ).group_by(PedidoModel.projeto_nome).order_by(
        func.count(PedidoModel.id).desc()
    ).limit(5)
    
    if usuario.role.value == 'consultor':
        projetos_query = projetos_query.where(PedidoModel.consultor_id == usuario.id)
    
    projetos_result = await session.execute(projetos_query)
    top_projetos = [{"nome": row.projeto_nome or "Sem projeto", "total": row.total} for row in projetos_result]
    
    # 5. Pedidos Críticos (parados há mais de 48h)
    limite_48h = datetime.now(timezone.utc) - timedelta(hours=48)
    
    criticos_query = select(func.count(PedidoModel.id)).where(
        PedidoModel.updated_at < limite_48h,
        PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
    )
    
    if usuario.role.value == 'consultor':
        criticos_query = criticos_query.where(PedidoModel.consultor_id == usuario.id)
    
    criticos_result = await session.execute(criticos_query)
    pedidos_criticos = criticos_result.scalar() or 0
    
    # 6. Total de Alunos Matriculados
    alunos_query = select(func.count(AlunoModel.id))
    alunos_result = await session.execute(alunos_query)
    total_alunos = alunos_result.scalar() or 0
    
    # 7. Matrículas por Mês (últimos 6 meses)
    seis_meses_atras = datetime.now(timezone.utc) - timedelta(days=180)
    
    # Query simplificada para SQLite
    matriculas_mes_query = select(
        func.strftime('%Y-%m', PedidoModel.created_at).label('mes'),
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.created_at >= seis_meses_atras
    ).group_by(
        func.strftime('%Y-%m', PedidoModel.created_at)
    ).order_by(
        func.strftime('%Y-%m', PedidoModel.created_at)
    )
    
    if usuario.role.value == 'consultor':
        matriculas_mes_query = matriculas_mes_query.where(PedidoModel.consultor_id == usuario.id)
    
    matriculas_mes_result = await session.execute(matriculas_mes_query)
    matriculas_por_mes = [{"mes": row.mes, "total": row.total} for row in matriculas_mes_result]
    
    # 8. Taxa de Conversão (aprovados / total)
    total_query = select(func.count(PedidoModel.id))
    if usuario.role.value == 'consultor':
        total_query = total_query.where(PedidoModel.consultor_id == usuario.id)
    total_result = await session.execute(total_query)
    total_pedidos = total_result.scalar() or 0
    
    aprovados_query = select(func.count(PedidoModel.id)).where(
        PedidoModel.status.in_(['aprovado', 'realizado', 'exportado'])
    )
    if usuario.role.value == 'consultor':
        aprovados_query = aprovados_query.where(PedidoModel.consultor_id == usuario.id)
    aprovados_result = await session.execute(aprovados_query)
    total_aprovados = aprovados_result.scalar() or 0
    
    taxa_conversao = (total_aprovados / total_pedidos * 100) if total_pedidos > 0 else 0
    
    # 9. Contagem por Status (para o card "Solicitações por Status")
    por_status = {
        'pendente': funil_data.get('pendente', 0),
        'em_analise': funil_data.get('em_analise', 0),
        'documentacao_pendente': funil_data.get('documentacao_pendente', 0),
        'aprovado': funil_data.get('aprovado', 0),
        'realizado': funil_data.get('realizado', 0),
        'exportado': funil_data.get('exportado', 0),
        'cancelado': funil_data.get('cancelado', 0),
        'rejeitado': funil_data.get('rejeitado', 0),
    }
    
    return {
        "funil": funil,
        "tempo_medio_dias": round(tempo_medio, 1),
        "top_empresas": top_empresas,
        "top_projetos": top_projetos,
        "pedidos_criticos": pedidos_criticos,
        "total_alunos": total_alunos,
        "matriculas_por_mes": matriculas_por_mes,
        "taxa_conversao": round(taxa_conversao, 1),
        "total_pedidos": total_pedidos,
        "por_status": por_status
    }


@router.get("/buscar/protocolo/{numero_protocolo}", response_model=PedidoResponseDTO)
async def buscar_por_protocolo(
    numero_protocolo: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Busca pedido por número de protocolo (ex: CM-2026-0001)"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    pedido = await pedido_repo.buscar_por_protocolo(numero_protocolo)
    if not pedido:
        raise HTTPException(404, f"Pedido com protocolo {numero_protocolo} não encontrado")
    
    # Verificar permissão (consultor só vê os próprios)
    if usuario.role == "consultor" and pedido.consultor_id != usuario.id:
        raise HTTPException(403, "Sem permissão para visualizar este pedido")
    
    return PedidoResponseDTO(**pedido.to_dict())


@router.get("/exportar/totvs")
async def exportar_totvs(
    formato: str = Query(default="xlsx", pattern="^(xlsx|csv)$"),
    deps: tuple = Depends(require_permission("pedido:exportar"))
):
    """Exporta pedidos realizados para formato TOTVS"""
    usuario, session = deps
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    gerar_exportacao_uc = GerarExportacaoTOTVSUseCase(pedido_repo, auditoria_repo)
    arquivo, content_type, nome_arquivo = await gerar_exportacao_uc.executar(usuario, formato)
    
    return StreamingResponse(
        arquivo,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={nome_arquivo}"
        }
    )


@router.get("/{pedido_id}", response_model=PedidoResponseDTO)
async def buscar_pedido(
    pedido_id: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Busca pedido por ID"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    return await consultar_pedidos_uc.buscar_por_id(pedido_id, usuario)


@router.get("/{pedido_id}/timeline")
async def buscar_timeline_pedido(
    pedido_id: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna timeline de auditoria de um pedido"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    usuario_repo = UsuarioRepository(session)
    
    # Verificar se pedido existe e se usuário tem acesso
    pedido = await pedido_repo.buscar_por_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Consultor só vê os próprios pedidos
    if usuario.role.value == 'consultor' and pedido.consultor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar este pedido")
    
    # Buscar registros de auditoria
    result = await session.execute(
        select(AuditoriaModel)
        .where(AuditoriaModel.pedido_id == pedido_id)
        .order_by(AuditoriaModel.timestamp.asc())  # Ordem cronológica
    )
    auditorias = result.scalars().all()
    
    # Buscar nomes dos usuários
    usuario_ids = list(set(a.usuario_id for a in auditorias))
    usuarios_dict = {}
    for uid in usuario_ids:
        u = await usuario_repo.buscar_por_id(uid)
        if u:
            usuarios_dict[uid] = u.nome
    
    # Mapear ações para labels amigáveis
    ACOES_LABELS = {
        "CRIACAO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "PEDIDO_CRIADO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "STATUS_ATUALIZADO": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "ATUALIZACAO_STATUS": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "PEDIDO_EXPORTADO": {"label": "Exportado para TOTVS", "icon": "download", "color": "green"},
        "EXPORTACAO": {"label": "Exportado para TOTVS", "icon": "download", "color": "green"},
        "DOCUMENTACAO_SOLICITADA": {"label": "Documentação Solicitada", "icon": "file", "color": "orange"},
        "PEDIDO_APROVADO": {"label": "Solicitação Aprovada", "icon": "check", "color": "green"},
        "PEDIDO_REALIZADO": {"label": "Matrícula Realizada", "icon": "check-circle", "color": "green"},
        "PEDIDO_CANCELADO": {"label": "Solicitação Cancelada", "icon": "x", "color": "red"},
    }
    
    # Construir timeline
    timeline = []
    for audit in auditorias:
        acao_info = ACOES_LABELS.get(audit.acao, {"label": audit.acao, "icon": "circle", "color": "gray"})
        
        # Extrair detalhes relevantes
        detalhes_str = ""
        if audit.detalhes:
            if "status_anterior" in audit.detalhes and "status_novo" in audit.detalhes:
                status_ant = audit.detalhes.get("status_anterior", "").replace("_", " ").title()
                status_novo = audit.detalhes.get("status_novo", "").replace("_", " ").title()
                detalhes_str = f"De '{status_ant}' para '{status_novo}'"
            elif "motivo" in audit.detalhes:
                detalhes_str = audit.detalhes.get("motivo", "")
            elif "formato" in audit.detalhes:
                detalhes_str = f"Formato: {audit.detalhes.get('formato', '').upper()}"
        
        timeline.append({
            "id": audit.id,
            "acao": audit.acao,
            "acao_label": acao_info["label"],
            "icon": acao_info["icon"],
            "color": acao_info["color"],
            "usuario_id": audit.usuario_id,
            "usuario_nome": usuarios_dict.get(audit.usuario_id, "Usuário Desconhecido"),
            "detalhes": detalhes_str,
            "detalhes_raw": audit.detalhes,
            "timestamp": audit.timestamp.isoformat() if audit.timestamp else None
        })
    
    return {
        "pedido_id": pedido_id,
        "numero_protocolo": pedido.numero_protocolo,
        "total_eventos": len(timeline),
        "timeline": timeline
    }


@router.patch("/{pedido_id}/status", response_model=PedidoResponseDTO)
async def atualizar_status(
    pedido_id: str,
    request: AtualizarStatusDTO,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza status do pedido"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    atualizar_status_uc = AtualizarStatusPedidoUseCase(pedido_repo, auditoria_repo)
    pedido = await atualizar_status_uc.executar(pedido_id, request, usuario)
    return PedidoResponseDTO(**pedido.to_dict())
