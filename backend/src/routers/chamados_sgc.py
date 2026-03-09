"""
Router para Chamados SGC Plus
Gerencia solicitações de matrícula BMP recebidas pelo SGC+
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

from .dependencies import get_current_user, get_db_session
from ..domain.entities import Usuario

router = APIRouter(prefix="/chamados-sgc", tags=["Chamados SGC"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ChamadoCreate(BaseModel):
    numero_ticket: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_abertura: datetime
    data_previsao_inicio: Optional[datetime] = None
    data_previsao_fim: Optional[datetime] = None
    prioridade: int = 0
    critico: bool = False
    sla_horas: float = 32.0
    solicitante_nome: Optional[str] = None
    solicitante_telefone: Optional[str] = None
    solicitante_unidade: Optional[str] = None
    area: Optional[str] = None
    classificacao: Optional[str] = "Matrícula"
    produto: Optional[str] = "MATRÍCULA BMP"
    dono_produto: Optional[str] = None
    tecnico_responsavel: Optional[str] = None
    pedido_id: Optional[str] = None
    # Campos do Formulário SGC Plus BMP
    codigo_curso: Optional[str] = None
    nome_curso: Optional[str] = None
    turno: Optional[str] = None
    periodo_letivo: Optional[str] = None
    quantidade_vagas: Optional[int] = None
    modalidade: Optional[str] = None  # CAP, IP, CAI, CQPH, CQP
    forma_pagamento: Optional[str] = None  # Empresa, Aluno, Gratuidade Regimental
    cont: Optional[str] = None
    requisito_acesso: Optional[str] = None
    empresa_nome: Optional[str] = None
    empresa_contato: Optional[str] = None
    empresa_email: Optional[str] = None
    empresa_telefone: Optional[str] = None
    data_inicio_curso: Optional[datetime] = None
    data_fim_curso: Optional[datetime] = None
    documentos_obrigatorios: Optional[str] = None


class ChamadoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_previsao_inicio: Optional[datetime] = None
    data_previsao_fim: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None
    status: Optional[str] = None
    prioridade: Optional[int] = None
    critico: Optional[bool] = None
    sla_pausado: Optional[bool] = None
    tecnico_responsavel: Optional[str] = None
    pedido_id: Optional[str] = None
    # Campos do Formulário SGC Plus BMP
    codigo_curso: Optional[str] = None
    nome_curso: Optional[str] = None
    turno: Optional[str] = None
    periodo_letivo: Optional[str] = None
    quantidade_vagas: Optional[int] = None
    modalidade: Optional[str] = None
    forma_pagamento: Optional[str] = None
    cont: Optional[str] = None
    requisito_acesso: Optional[str] = None
    empresa_nome: Optional[str] = None
    empresa_contato: Optional[str] = None
    empresa_email: Optional[str] = None
    empresa_telefone: Optional[str] = None
    data_inicio_curso: Optional[datetime] = None
    data_fim_curso: Optional[datetime] = None
    documentos_obrigatorios: Optional[str] = None


class AndamentoCreate(BaseModel):
    andamento: str
    observacao: Optional[str] = None


class InteracaoCreate(BaseModel):
    tipo: str = "comunicacao"
    mensagem: str


class EsforcoCreate(BaseModel):
    horas: float
    data: str  # YYYY-MM-DD
    descricao: Optional[str] = None


class ChamadoResponse(BaseModel):
    id: str
    numero_ticket: str
    titulo: Optional[str]
    descricao: Optional[str]
    data_abertura: datetime
    data_previsao_fim: Optional[datetime]
    data_fechamento: Optional[datetime]
    status: str
    prioridade: int
    critico: bool
    sla_horas: float
    sla_consumido: float
    sla_pausado: bool
    solicitante_nome: Optional[str]
    solicitante_unidade: Optional[str]
    area: Optional[str]
    classificacao: Optional[str]
    produto: Optional[str]
    tecnico_responsavel: Optional[str]
    pedido_id: Optional[str]
    created_at: datetime


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("")
async def listar_chamados(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    tecnico: Optional[str] = None,
    busca: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os chamados SGC com filtros"""
    
    # Base query
    where_clauses = []
    params = {}
    
    if status:
        where_clauses.append("status = :status")
        params["status"] = status
    
    if tecnico:
        where_clauses.append("tecnico_responsavel LIKE :tecnico")
        params["tecnico"] = f"%{tecnico}%"
    
    if busca:
        where_clauses.append("""
            (numero_ticket LIKE :busca OR 
             titulo LIKE :busca OR 
             solicitante_nome LIKE :busca OR
             descricao LIKE :busca)
        """)
        params["busca"] = f"%{busca}%"
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Contar total
    count_result = await session.execute(
        text(f"SELECT COUNT(*) FROM chamados_sgc WHERE {where_sql}"),
        params
    )
    total = count_result.scalar()
    
    # Buscar chamados
    offset = (pagina - 1) * por_pagina
    params["limit"] = por_pagina
    params["offset"] = offset
    
    result = await session.execute(
        text(f"""
            SELECT id, numero_ticket, titulo, descricao, data_abertura,
                   data_previsao_fim, data_fechamento, status, prioridade,
                   critico, sla_horas, sla_consumido, sla_pausado,
                   solicitante_nome, solicitante_unidade, area, classificacao,
                   produto, tecnico_responsavel, pedido_id, created_at
            FROM chamados_sgc 
            WHERE {where_sql}
            ORDER BY 
                CASE WHEN status = 'backlog' THEN 1
                     WHEN status = 'em_atendimento' THEN 2
                     WHEN status = 'aguardando_retorno' THEN 3
                     ELSE 4 END,
                critico DESC,
                data_previsao_fim ASC
            LIMIT :limit OFFSET :offset
        """),
        params
    )
    
    chamados = []
    for row in result.fetchall():
        chamados.append({
            "id": row[0],
            "numero_ticket": row[1],
            "titulo": row[2],
            "descricao": row[3],
            "data_abertura": row[4],
            "data_previsao_fim": row[5],
            "data_fechamento": row[6],
            "status": row[7],
            "prioridade": row[8],
            "critico": bool(row[9]),
            "sla_horas": float(row[10] or 32),
            "sla_consumido": float(row[11] or 0),
            "sla_pausado": bool(row[12]),
            "solicitante_nome": row[13],
            "solicitante_unidade": row[14],
            "area": row[15],
            "classificacao": row[16],
            "produto": row[17],
            "tecnico_responsavel": row[18],
            "pedido_id": row[19],
            "created_at": row[20]
        })
    
    return {
        "chamados": chamados,
        "paginacao": {
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_itens": total,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    }


@router.get("/dashboard")
async def dashboard_chamados(
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Dashboard resumo dos chamados"""
    
    # Total por status
    result = await session.execute(text("""
        SELECT status, COUNT(*) FROM chamados_sgc GROUP BY status
    """))
    por_status = {row[0]: row[1] for row in result.fetchall()}
    
    # Chamados críticos abertos
    result = await session.execute(text("""
        SELECT COUNT(*) FROM chamados_sgc 
        WHERE critico = 1 AND data_fechamento IS NULL
    """))
    criticos = result.scalar() or 0
    
    # Chamados com SLA próximo de estourar (> 80%)
    result = await session.execute(text("""
        SELECT COUNT(*) FROM chamados_sgc 
        WHERE data_fechamento IS NULL 
        AND sla_consumido >= (sla_horas * 0.8)
    """))
    sla_critico = result.scalar() or 0
    
    # Total abertos
    result = await session.execute(text("""
        SELECT COUNT(*) FROM chamados_sgc WHERE data_fechamento IS NULL
    """))
    total_abertos = result.scalar() or 0
    
    # Fechados hoje
    result = await session.execute(text("""
        SELECT COUNT(*) FROM chamados_sgc 
        WHERE DATE(data_fechamento) = DATE('now')
    """))
    fechados_hoje = result.scalar() or 0
    
    return {
        "total_abertos": total_abertos,
        "criticos": criticos,
        "sla_critico": sla_critico,
        "fechados_hoje": fechados_hoje,
        "por_status": por_status
    }


@router.get("/{chamado_id}")
async def obter_chamado(
    chamado_id: str,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Obtém detalhes de um chamado com andamentos e interações"""
    
    # Buscar chamado
    result = await session.execute(
        text("SELECT * FROM chamados_sgc WHERE id = :id"),
        {"id": chamado_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Buscar andamentos
    andamentos_result = await session.execute(
        text("""
            SELECT id, andamento, observacao, usuario_nome, created_at
            FROM chamados_sgc_andamentos 
            WHERE chamado_id = :id
            ORDER BY created_at DESC
        """),
        {"id": chamado_id}
    )
    andamentos = [
        {"id": r[0], "andamento": r[1], "observacao": r[2], "usuario": r[3], "data": r[4]}
        for r in andamentos_result.fetchall()
    ]
    
    # Buscar interações
    interacoes_result = await session.execute(
        text("""
            SELECT id, tipo, mensagem, usuario_nome, created_at
            FROM chamados_sgc_interacoes 
            WHERE chamado_id = :id
            ORDER BY created_at DESC
        """),
        {"id": chamado_id}
    )
    interacoes = [
        {"id": r[0], "tipo": r[1], "mensagem": r[2], "usuario": r[3], "data": r[4]}
        for r in interacoes_result.fetchall()
    ]
    
    # Buscar esforço
    esforco_result = await session.execute(
        text("""
            SELECT id, analista_nome, horas, data, descricao, created_at
            FROM chamados_sgc_esforco 
            WHERE chamado_id = :id
            ORDER BY data DESC
        """),
        {"id": chamado_id}
    )
    esforco = [
        {"id": r[0], "analista": r[1], "horas": float(r[2]), "data": r[3], "descricao": r[4]}
        for r in esforco_result.fetchall()
    ]
    
    # Calcular totais
    total_horas = sum(e["horas"] for e in esforco)
    
    return {
        "chamado": {
            "id": row[0],
            "numero_ticket": row[1],
            "titulo": row[2],
            "descricao": row[3],
            "data_abertura": row[4],
            "data_previsao_inicio": row[5],
            "data_previsao_fim": row[6],
            "data_fechamento": row[7],
            "status": row[8],
            "prioridade": row[9],
            "critico": bool(row[10]),
            "sla_horas": float(row[11] or 32),
            "sla_consumido": float(row[12] or 0),
            "sla_pausado": bool(row[13]),
            "solicitante_nome": row[14],
            "solicitante_telefone": row[15],
            "solicitante_unidade": row[16],
            "area": row[17],
            "classificacao": row[18],
            "produto": row[19],
            "dono_produto": row[20],
            "tecnico_responsavel": row[21],
            "pedido_id": row[22]
        },
        "andamentos": andamentos,
        "interacoes": interacoes,
        "esforco": esforco,
        "total_horas": total_horas
    }


@router.post("")
async def criar_chamado(
    data: ChamadoCreate,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Cria um novo chamado SGC"""
    
    chamado_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    await session.execute(
        text("""
            INSERT INTO chamados_sgc (
                id, numero_ticket, titulo, descricao, data_abertura,
                data_previsao_inicio, data_previsao_fim, status, prioridade,
                critico, sla_horas, solicitante_nome, solicitante_telefone,
                solicitante_unidade, area, classificacao, produto, dono_produto,
                tecnico_responsavel, pedido_id, criado_por_id, criado_por_nome,
                codigo_curso, nome_curso, turno, periodo_letivo, quantidade_vagas,
                modalidade, forma_pagamento, cont, requisito_acesso,
                empresa_nome, empresa_contato, empresa_email, empresa_telefone,
                data_inicio_curso, data_fim_curso, documentos_obrigatorios,
                created_at, updated_at
            ) VALUES (
                :id, :numero_ticket, :titulo, :descricao, :data_abertura,
                :data_previsao_inicio, :data_previsao_fim, 'backlog', :prioridade,
                :critico, :sla_horas, :solicitante_nome, :solicitante_telefone,
                :solicitante_unidade, :area, :classificacao, :produto, :dono_produto,
                :tecnico_responsavel, :pedido_id, :criado_por_id, :criado_por_nome,
                :codigo_curso, :nome_curso, :turno, :periodo_letivo, :quantidade_vagas,
                :modalidade, :forma_pagamento, :cont, :requisito_acesso,
                :empresa_nome, :empresa_contato, :empresa_email, :empresa_telefone,
                :data_inicio_curso, :data_fim_curso, :documentos_obrigatorios,
                :created_at, :updated_at
            )
        """),
        {
            "id": chamado_id,
            "numero_ticket": data.numero_ticket,
            "titulo": data.titulo,
            "descricao": data.descricao,
            "data_abertura": data.data_abertura.isoformat(),
            "data_previsao_inicio": data.data_previsao_inicio.isoformat() if data.data_previsao_inicio else None,
            "data_previsao_fim": data.data_previsao_fim.isoformat() if data.data_previsao_fim else None,
            "prioridade": data.prioridade,
            "critico": data.critico,
            "sla_horas": data.sla_horas,
            "solicitante_nome": data.solicitante_nome,
            "solicitante_telefone": data.solicitante_telefone,
            "solicitante_unidade": data.solicitante_unidade,
            "area": data.area,
            "classificacao": data.classificacao,
            "produto": data.produto,
            "dono_produto": data.dono_produto,
            "tecnico_responsavel": data.tecnico_responsavel,
            "pedido_id": data.pedido_id,
            "criado_por_id": current_user.id,
            "criado_por_nome": current_user.nome,
            # Novos campos do formulário SGC
            "codigo_curso": data.codigo_curso,
            "nome_curso": data.nome_curso,
            "turno": data.turno,
            "periodo_letivo": data.periodo_letivo,
            "quantidade_vagas": data.quantidade_vagas,
            "modalidade": data.modalidade,
            "forma_pagamento": data.forma_pagamento,
            "cont": data.cont,
            "requisito_acesso": data.requisito_acesso,
            "empresa_nome": data.empresa_nome,
            "empresa_contato": data.empresa_contato,
            "empresa_email": data.empresa_email,
            "empresa_telefone": data.empresa_telefone,
            "data_inicio_curso": data.data_inicio_curso.isoformat() if data.data_inicio_curso else None,
            "data_fim_curso": data.data_fim_curso.isoformat() if data.data_fim_curso else None,
            "documentos_obrigatorios": data.documentos_obrigatorios,
            "created_at": now,
            "updated_at": now
        }
    )
    
    # Criar andamento inicial
    await session.execute(
        text("""
            INSERT INTO chamados_sgc_andamentos (id, chamado_id, andamento, usuario_id, usuario_nome, created_at)
            VALUES (:id, :chamado_id, 'Backlog', :usuario_id, :usuario_nome, :created_at)
        """),
        {
            "id": str(uuid.uuid4()),
            "chamado_id": chamado_id,
            "usuario_id": current_user.id,
            "usuario_nome": current_user.nome,
            "created_at": now
        }
    )
    
    await session.commit()
    
    return {"id": chamado_id, "message": "Chamado criado com sucesso"}


@router.put("/{chamado_id}")
async def atualizar_chamado(
    chamado_id: str,
    data: ChamadoUpdate,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza um chamado"""
    
    # Verificar se existe
    result = await session.execute(
        text("SELECT id, status FROM chamados_sgc WHERE id = :id"),
        {"id": chamado_id}
    )
    chamado = result.fetchone()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    status_anterior = chamado[1]
    now = datetime.now(timezone.utc).isoformat()
    
    # Montar update dinâmico
    updates = []
    params = {"id": chamado_id, "updated_at": now, "atualizado_por_id": current_user.id, "atualizado_por_nome": current_user.nome}
    
    if data.titulo is not None:
        updates.append("titulo = :titulo")
        params["titulo"] = data.titulo
    if data.descricao is not None:
        updates.append("descricao = :descricao")
        params["descricao"] = data.descricao
    if data.status is not None:
        updates.append("status = :status")
        params["status"] = data.status
    if data.prioridade is not None:
        updates.append("prioridade = :prioridade")
        params["prioridade"] = data.prioridade
    if data.critico is not None:
        updates.append("critico = :critico")
        params["critico"] = data.critico
    if data.sla_pausado is not None:
        updates.append("sla_pausado = :sla_pausado")
        params["sla_pausado"] = data.sla_pausado
    if data.tecnico_responsavel is not None:
        updates.append("tecnico_responsavel = :tecnico_responsavel")
        params["tecnico_responsavel"] = data.tecnico_responsavel
    if data.pedido_id is not None:
        updates.append("pedido_id = :pedido_id")
        params["pedido_id"] = data.pedido_id
    if data.data_fechamento is not None:
        updates.append("data_fechamento = :data_fechamento")
        params["data_fechamento"] = data.data_fechamento.isoformat()
    
    updates.append("updated_at = :updated_at")
    updates.append("atualizado_por_id = :atualizado_por_id")
    updates.append("atualizado_por_nome = :atualizado_por_nome")
    
    await session.execute(
        text(f"UPDATE chamados_sgc SET {', '.join(updates)} WHERE id = :id"),
        params
    )
    
    # Se mudou status, criar andamento
    if data.status and data.status != status_anterior:
        status_map = {
            'backlog': 'Backlog',
            'em_atendimento': 'Em atendimento',
            'aguardando_retorno': 'Aguardando retorno',
            'concluido': 'Concluído',
            'cancelado': 'Cancelado'
        }
        await session.execute(
            text("""
                INSERT INTO chamados_sgc_andamentos (id, chamado_id, andamento, usuario_id, usuario_nome, created_at)
                VALUES (:id, :chamado_id, :andamento, :usuario_id, :usuario_nome, :created_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "chamado_id": chamado_id,
                "andamento": status_map.get(data.status, data.status),
                "usuario_id": current_user.id,
                "usuario_nome": current_user.nome,
                "created_at": now
            }
        )
    
    await session.commit()
    
    return {"message": "Chamado atualizado com sucesso"}


@router.post("/{chamado_id}/interacao")
async def adicionar_interacao(
    chamado_id: str,
    data: InteracaoCreate,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Adiciona uma interação/comunicação ao chamado"""
    
    now = datetime.now(timezone.utc).isoformat()
    
    await session.execute(
        text("""
            INSERT INTO chamados_sgc_interacoes (id, chamado_id, tipo, mensagem, usuario_id, usuario_nome, created_at)
            VALUES (:id, :chamado_id, :tipo, :mensagem, :usuario_id, :usuario_nome, :created_at)
        """),
        {
            "id": str(uuid.uuid4()),
            "chamado_id": chamado_id,
            "tipo": data.tipo,
            "mensagem": data.mensagem,
            "usuario_id": current_user.id,
            "usuario_nome": current_user.nome,
            "created_at": now
        }
    )
    
    await session.commit()
    
    return {"message": "Interação adicionada com sucesso"}


@router.post("/{chamado_id}/esforco")
async def adicionar_esforco(
    chamado_id: str,
    data: EsforcoCreate,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Registra horas de esforço no chamado"""
    
    now = datetime.now(timezone.utc).isoformat()
    
    await session.execute(
        text("""
            INSERT INTO chamados_sgc_esforco (id, chamado_id, analista_id, analista_nome, horas, data, descricao, created_at)
            VALUES (:id, :chamado_id, :analista_id, :analista_nome, :horas, :data, :descricao, :created_at)
        """),
        {
            "id": str(uuid.uuid4()),
            "chamado_id": chamado_id,
            "analista_id": current_user.id,
            "analista_nome": current_user.nome,
            "horas": data.horas,
            "data": data.data,
            "descricao": data.descricao,
            "created_at": now
        }
    )
    
    # Atualizar SLA consumido
    await session.execute(
        text("""
            UPDATE chamados_sgc 
            SET sla_consumido = sla_consumido + :horas
            WHERE id = :chamado_id
        """),
        {"horas": data.horas, "chamado_id": chamado_id}
    )
    
    await session.commit()
    
    return {"message": "Esforço registrado com sucesso"}
