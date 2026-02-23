"""Router de Apoio Cognitivo - Meu Dia e Base de Conhecimento"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.domain.entities import Usuario
from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/apoio", tags=["Apoio Cognitivo"])


# ==================== MODELOS ====================

from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.persistence.database import Base


class TarefaDiariaModel(Base):
    """Modelo para tarefas do checklist diário"""
    __tablename__ = "tarefas_diarias"
    
    id = Column(String(36), primary_key=True)
    usuario_id = Column(String(36), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    categoria = Column(String(50), nullable=True)  # rotina, pendencia, lembrete, outro
    prioridade = Column(Integer, default=2)  # 1=alta, 2=media, 3=baixa
    recorrente = Column(Boolean, default=False)  # Se repete todos os dias
    dias_semana = Column(String(20), nullable=True)  # "1,2,3,4,5" = seg a sex
    horario_sugerido = Column(String(5), nullable=True)  # "09:00"
    concluida = Column(Boolean, default=False)
    data_conclusao = Column(DateTime, nullable=True)
    data_tarefa = Column(Date, nullable=True)  # Data específica da tarefa
    ordem = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ArtigoConhecimentoModel(Base):
    """Modelo para artigos da base de conhecimento"""
    __tablename__ = "artigos_conhecimento"
    
    id = Column(String(36), primary_key=True)
    titulo = Column(String(200), nullable=False)
    conteudo = Column(Text, nullable=False)
    resumo = Column(Text, nullable=True)  # Resumo curto para exibição
    categoria = Column(String(50), nullable=False)  # procedimento, faq, documento, dica
    tags = Column(String(500), nullable=True)  # Tags separadas por vírgula
    icone = Column(String(50), nullable=True)  # Nome do ícone lucide
    destaque = Column(Boolean, default=False)  # Se aparece na home
    ordem = Column(Integer, default=0)
    visualizacoes = Column(Integer, default=0)
    criado_por_id = Column(String(36), nullable=True)
    criado_por_nome = Column(String(200), nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LembreteModel(Base):
    """Modelo para lembretes personalizados"""
    __tablename__ = "lembretes"
    
    id = Column(String(36), primary_key=True)
    usuario_id = Column(String(36), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    data_lembrete = Column(DateTime, nullable=False)
    tipo = Column(String(30), nullable=True)  # contato, reuniao, prazo, outro
    referencia_id = Column(String(36), nullable=True)  # ID de pedido/pendência relacionado
    referencia_tipo = Column(String(30), nullable=True)  # pedido, pendencia
    notificado = Column(Boolean, default=False)
    concluido = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==================== DTOs ====================

class TarefaRequest(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = None
    categoria: Optional[str] = "outro"
    prioridade: Optional[int] = 2
    recorrente: Optional[bool] = False
    dias_semana: Optional[str] = None
    horario_sugerido: Optional[str] = None
    data_tarefa: Optional[str] = None  # YYYY-MM-DD
    ordem: Optional[int] = 0


class ArtigoRequest(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=200)
    conteudo: str = Field(..., min_length=10)
    resumo: Optional[str] = None
    categoria: str = "procedimento"
    tags: Optional[str] = None
    icone: Optional[str] = None
    destaque: Optional[bool] = False
    ordem: Optional[int] = 0


class LembreteRequest(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = None
    data_lembrete: str  # ISO format
    tipo: Optional[str] = "outro"
    referencia_id: Optional[str] = None
    referencia_tipo: Optional[str] = None


# ==================== CATEGORIAS ====================

CATEGORIAS_TAREFA = [
    {"value": "rotina", "label": "Rotina Diária", "cor": "blue"},
    {"value": "pendencia", "label": "Pendência", "cor": "orange"},
    {"value": "lembrete", "label": "Lembrete", "cor": "purple"},
    {"value": "reuniao", "label": "Reunião", "cor": "green"},
    {"value": "outro", "label": "Outro", "cor": "gray"},
]

CATEGORIAS_ARTIGO = [
    {"value": "procedimento", "label": "Procedimento", "icone": "FileText"},
    {"value": "faq", "label": "Perguntas Frequentes", "icone": "HelpCircle"},
    {"value": "documento", "label": "Documento", "icone": "File"},
    {"value": "dica", "label": "Dica Rápida", "icone": "Lightbulb"},
    {"value": "contato", "label": "Informação de Contato", "icone": "Phone"},
]


# ==================== MEU DIA ====================

@router.get("/meu-dia")
async def meu_dia(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna o resumo do dia do usuário"""
    from src.infrastructure.persistence.models import PendenciaModel, PedidoModel
    from src.infrastructure.persistence.models_contatos import ContatoModel
    
    hoje = date.today()
    dia_semana = str(hoje.weekday() + 1)  # 1=segunda, 7=domingo
    
    # Buscar tarefas do dia (específicas + recorrentes do dia da semana)
    tarefas_query = select(TarefaDiariaModel).where(
        and_(
            TarefaDiariaModel.usuario_id == usuario.id,
            TarefaDiariaModel.ativo == True,
            or_(
                TarefaDiariaModel.data_tarefa == hoje,
                and_(
                    TarefaDiariaModel.recorrente == True,
                    or_(
                        TarefaDiariaModel.dias_semana == None,
                        TarefaDiariaModel.dias_semana.contains(dia_semana)
                    )
                )
            )
        )
    ).order_by(TarefaDiariaModel.ordem, TarefaDiariaModel.prioridade)
    
    tarefas_result = await session.execute(tarefas_query)
    tarefas = tarefas_result.scalars().all()
    
    # Buscar lembretes do dia
    inicio_dia = datetime.combine(hoje, datetime.min.time()).replace(tzinfo=timezone.utc)
    fim_dia = datetime.combine(hoje, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    lembretes_query = select(LembreteModel).where(
        and_(
            LembreteModel.usuario_id == usuario.id,
            LembreteModel.ativo == True,
            LembreteModel.concluido == False,
            LembreteModel.data_lembrete >= inicio_dia,
            LembreteModel.data_lembrete <= fim_dia
        )
    ).order_by(LembreteModel.data_lembrete)
    
    lembretes_result = await session.execute(lembretes_query)
    lembretes = lembretes_result.scalars().all()
    
    # Buscar retornos de contato pendentes (usando a tabela de contatos correta)
    retornos_query = select(func.count(ContatoModel.id)).where(
        and_(
            ContatoModel.data_retorno != None,
            ContatoModel.retorno_realizado == False,
            ContatoModel.data_retorno <= fim_dia
        )
    )
    retornos_result = await session.execute(retornos_query)
    total_retornos = retornos_result.scalar() or 0
    
    # Contagem de pendências em aberto
    pendencias_query = await session.execute(
        select(func.count(PendenciaModel.id)).where(
            PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'reenvio_necessario'])
        )
    )
    total_pendencias = pendencias_query.scalar() or 0
    
    # Pedidos em análise
    pedidos_query = await session.execute(
        select(func.count(PedidoModel.id)).where(
            PedidoModel.status.in_(['em_analise', 'documentacao_pendente'])
        )
    )
    total_pedidos_andamento = pedidos_query.scalar() or 0
    
    return {
        "data": hoje.isoformat(),
        "dia_semana": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][hoje.weekday()],
        "saudacao": _get_saudacao(),
        "tarefas": [
            {
                "id": t.id,
                "titulo": t.titulo,
                "descricao": t.descricao,
                "categoria": t.categoria,
                "prioridade": t.prioridade,
                "horario_sugerido": t.horario_sugerido,
                "concluida": t.concluida,
                "recorrente": t.recorrente
            }
            for t in tarefas
        ],
        "lembretes": [
            {
                "id": l.id,
                "titulo": l.titulo,
                "descricao": l.descricao,
                "horario": l.data_lembrete.strftime("%H:%M") if l.data_lembrete else None,
                "tipo": l.tipo
            }
            for l in lembretes
        ],
        "retornos_pendentes": total_retornos,
        "resumo": {
            "tarefas_total": len(tarefas),
            "tarefas_concluidas": len([t for t in tarefas if t.concluida]),
            "pendencias_abertas": total_pendencias,
            "pedidos_andamento": total_pedidos_andamento,
            "lembretes_hoje": len(lembretes)
        }
    }


def _get_saudacao():
    """Retorna saudação baseada no horário"""
    hora = datetime.now().hour
    if hora < 12:
        return "Bom dia"
    elif hora < 18:
        return "Boa tarde"
    return "Boa noite"


# ==================== TAREFAS ====================

@router.get("/tarefas")
async def listar_tarefas(
    data: Optional[str] = None,  # YYYY-MM-DD
    categoria: Optional[str] = None,
    concluida: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista tarefas do usuário"""
    query = select(TarefaDiariaModel).where(
        and_(
            TarefaDiariaModel.usuario_id == usuario.id,
            TarefaDiariaModel.ativo == True
        )
    )
    
    if data:
        data_filtro = datetime.strptime(data, "%Y-%m-%d").date()
        dia_semana = str(data_filtro.weekday() + 1)
        query = query.where(
            or_(
                TarefaDiariaModel.data_tarefa == data_filtro,
                and_(
                    TarefaDiariaModel.recorrente == True,
                    or_(
                        TarefaDiariaModel.dias_semana == None,
                        TarefaDiariaModel.dias_semana.contains(dia_semana)
                    )
                )
            )
        )
    
    if categoria:
        query = query.where(TarefaDiariaModel.categoria == categoria)
    
    if concluida is not None:
        query = query.where(TarefaDiariaModel.concluida == concluida)
    
    query = query.order_by(TarefaDiariaModel.ordem, TarefaDiariaModel.prioridade)
    
    result = await session.execute(query)
    tarefas = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "titulo": t.titulo,
            "descricao": t.descricao,
            "categoria": t.categoria,
            "prioridade": t.prioridade,
            "recorrente": t.recorrente,
            "dias_semana": t.dias_semana,
            "horario_sugerido": t.horario_sugerido,
            "concluida": t.concluida,
            "data_tarefa": t.data_tarefa.isoformat() if t.data_tarefa else None,
            "ordem": t.ordem
        }
        for t in tarefas
    ]


@router.post("/tarefas")
async def criar_tarefa(
    request: TarefaRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria uma nova tarefa"""
    tarefa = TarefaDiariaModel(
        id=str(uuid.uuid4()),
        usuario_id=usuario.id,
        titulo=request.titulo,
        descricao=request.descricao,
        categoria=request.categoria,
        prioridade=request.prioridade,
        recorrente=request.recorrente,
        dias_semana=request.dias_semana,
        horario_sugerido=request.horario_sugerido,
        data_tarefa=datetime.strptime(request.data_tarefa, "%Y-%m-%d").date() if request.data_tarefa else None,
        ordem=request.ordem
    )
    
    session.add(tarefa)
    await session.commit()
    
    return {
        "id": tarefa.id,
        "titulo": tarefa.titulo,
        "mensagem": "Tarefa criada com sucesso"
    }


@router.put("/tarefas/{tarefa_id}")
async def atualizar_tarefa(
    tarefa_id: str,
    request: TarefaRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza uma tarefa"""
    result = await session.execute(
        select(TarefaDiariaModel).where(
            and_(
                TarefaDiariaModel.id == tarefa_id,
                TarefaDiariaModel.usuario_id == usuario.id
            )
        )
    )
    tarefa = result.scalar_one_or_none()
    
    if not tarefa:
        raise HTTPException(404, "Tarefa não encontrada")
    
    tarefa.titulo = request.titulo
    tarefa.descricao = request.descricao
    tarefa.categoria = request.categoria
    tarefa.prioridade = request.prioridade
    tarefa.recorrente = request.recorrente
    tarefa.dias_semana = request.dias_semana
    tarefa.horario_sugerido = request.horario_sugerido
    tarefa.ordem = request.ordem
    if request.data_tarefa:
        tarefa.data_tarefa = datetime.strptime(request.data_tarefa, "%Y-%m-%d").date()
    
    await session.commit()
    return {"mensagem": "Tarefa atualizada com sucesso"}


@router.patch("/tarefas/{tarefa_id}/concluir")
async def concluir_tarefa(
    tarefa_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Marca tarefa como concluída/não concluída"""
    result = await session.execute(
        select(TarefaDiariaModel).where(
            and_(
                TarefaDiariaModel.id == tarefa_id,
                TarefaDiariaModel.usuario_id == usuario.id
            )
        )
    )
    tarefa = result.scalar_one_or_none()
    
    if not tarefa:
        raise HTTPException(404, "Tarefa não encontrada")
    
    tarefa.concluida = not tarefa.concluida
    tarefa.data_conclusao = datetime.now(timezone.utc) if tarefa.concluida else None
    
    await session.commit()
    return {
        "concluida": tarefa.concluida,
        "mensagem": "Tarefa concluída!" if tarefa.concluida else "Tarefa reaberta"
    }


@router.delete("/tarefas/{tarefa_id}")
async def deletar_tarefa(
    tarefa_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Remove uma tarefa"""
    result = await session.execute(
        select(TarefaDiariaModel).where(
            and_(
                TarefaDiariaModel.id == tarefa_id,
                TarefaDiariaModel.usuario_id == usuario.id
            )
        )
    )
    tarefa = result.scalar_one_or_none()
    
    if not tarefa:
        raise HTTPException(404, "Tarefa não encontrada")
    
    tarefa.ativo = False
    await session.commit()
    return {"mensagem": "Tarefa removida com sucesso"}


# ==================== BASE DE CONHECIMENTO ====================

@router.get("/conhecimento/categorias")
async def listar_categorias_conhecimento():
    """Lista categorias da base de conhecimento"""
    return CATEGORIAS_ARTIGO


@router.get("/conhecimento")
async def listar_artigos(
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
    destaque: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista artigos da base de conhecimento"""
    query = select(ArtigoConhecimentoModel).where(ArtigoConhecimentoModel.ativo == True)
    
    if categoria:
        query = query.where(ArtigoConhecimentoModel.categoria == categoria)
    
    if destaque is not None:
        query = query.where(ArtigoConhecimentoModel.destaque == destaque)
    
    if busca:
        query = query.where(
            or_(
                ArtigoConhecimentoModel.titulo.ilike(f"%{busca}%"),
                ArtigoConhecimentoModel.conteudo.ilike(f"%{busca}%"),
                ArtigoConhecimentoModel.tags.ilike(f"%{busca}%")
            )
        )
    
    query = query.order_by(desc(ArtigoConhecimentoModel.destaque), ArtigoConhecimentoModel.ordem, ArtigoConhecimentoModel.titulo)
    
    result = await session.execute(query)
    artigos = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "titulo": a.titulo,
            "resumo": a.resumo,
            "categoria": a.categoria,
            "tags": a.tags.split(",") if a.tags else [],
            "icone": a.icone,
            "destaque": a.destaque,
            "visualizacoes": a.visualizacoes
        }
        for a in artigos
    ]


@router.get("/conhecimento/{artigo_id}")
async def buscar_artigo(
    artigo_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna detalhes de um artigo"""
    result = await session.execute(
        select(ArtigoConhecimentoModel).where(
            and_(
                ArtigoConhecimentoModel.id == artigo_id,
                ArtigoConhecimentoModel.ativo == True
            )
        )
    )
    artigo = result.scalar_one_or_none()
    
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado")
    
    # Incrementar visualizações
    artigo.visualizacoes += 1
    await session.commit()
    
    return {
        "id": artigo.id,
        "titulo": artigo.titulo,
        "conteudo": artigo.conteudo,
        "resumo": artigo.resumo,
        "categoria": artigo.categoria,
        "tags": artigo.tags.split(",") if artigo.tags else [],
        "icone": artigo.icone,
        "destaque": artigo.destaque,
        "visualizacoes": artigo.visualizacoes,
        "criado_por": artigo.criado_por_nome,
        "created_at": artigo.created_at.isoformat() if artigo.created_at else None,
        "updated_at": artigo.updated_at.isoformat() if artigo.updated_at else None
    }


@router.post("/conhecimento")
async def criar_artigo(
    request: ArtigoRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria um novo artigo (Admin)"""
    if usuario.role != 'admin':
        raise HTTPException(403, "Apenas administradores podem criar artigos")
    
    artigo = ArtigoConhecimentoModel(
        id=str(uuid.uuid4()),
        titulo=request.titulo,
        conteudo=request.conteudo,
        resumo=request.resumo,
        categoria=request.categoria,
        tags=request.tags,
        icone=request.icone,
        destaque=request.destaque,
        ordem=request.ordem,
        criado_por_id=usuario.id,
        criado_por_nome=usuario.nome
    )
    
    session.add(artigo)
    await session.commit()
    
    return {
        "id": artigo.id,
        "titulo": artigo.titulo,
        "mensagem": "Artigo criado com sucesso"
    }


@router.put("/conhecimento/{artigo_id}")
async def atualizar_artigo(
    artigo_id: str,
    request: ArtigoRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza um artigo (Admin)"""
    if usuario.role != 'admin':
        raise HTTPException(403, "Apenas administradores podem editar artigos")
    
    result = await session.execute(
        select(ArtigoConhecimentoModel).where(ArtigoConhecimentoModel.id == artigo_id)
    )
    artigo = result.scalar_one_or_none()
    
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado")
    
    artigo.titulo = request.titulo
    artigo.conteudo = request.conteudo
    artigo.resumo = request.resumo
    artigo.categoria = request.categoria
    artigo.tags = request.tags
    artigo.icone = request.icone
    artigo.destaque = request.destaque
    artigo.ordem = request.ordem
    
    await session.commit()
    return {"mensagem": "Artigo atualizado com sucesso"}


@router.delete("/conhecimento/{artigo_id}")
async def deletar_artigo(
    artigo_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Remove um artigo (Admin)"""
    if usuario.role != 'admin':
        raise HTTPException(403, "Apenas administradores podem remover artigos")
    
    result = await session.execute(
        select(ArtigoConhecimentoModel).where(ArtigoConhecimentoModel.id == artigo_id)
    )
    artigo = result.scalar_one_or_none()
    
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado")
    
    artigo.ativo = False
    await session.commit()
    return {"mensagem": "Artigo removido com sucesso"}


# ==================== LEMBRETES ====================

@router.get("/lembretes")
async def listar_lembretes(
    pendentes: Optional[bool] = True,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista lembretes do usuário"""
    query = select(LembreteModel).where(
        and_(
            LembreteModel.usuario_id == usuario.id,
            LembreteModel.ativo == True
        )
    )
    
    if pendentes:
        query = query.where(LembreteModel.concluido == False)
    
    query = query.order_by(LembreteModel.data_lembrete)
    
    result = await session.execute(query)
    lembretes = result.scalars().all()
    
    return [
        {
            "id": l.id,
            "titulo": l.titulo,
            "descricao": l.descricao,
            "data_lembrete": l.data_lembrete.isoformat() if l.data_lembrete else None,
            "tipo": l.tipo,
            "referencia_id": l.referencia_id,
            "referencia_tipo": l.referencia_tipo,
            "concluido": l.concluido
        }
        for l in lembretes
    ]


@router.post("/lembretes")
async def criar_lembrete(
    request: LembreteRequest,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria um novo lembrete"""
    lembrete = LembreteModel(
        id=str(uuid.uuid4()),
        usuario_id=usuario.id,
        titulo=request.titulo,
        descricao=request.descricao,
        data_lembrete=datetime.fromisoformat(request.data_lembrete.replace('Z', '+00:00')),
        tipo=request.tipo,
        referencia_id=request.referencia_id,
        referencia_tipo=request.referencia_tipo
    )
    
    session.add(lembrete)
    await session.commit()
    
    return {
        "id": lembrete.id,
        "mensagem": "Lembrete criado com sucesso"
    }


@router.patch("/lembretes/{lembrete_id}/concluir")
async def concluir_lembrete(
    lembrete_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Marca lembrete como concluído"""
    result = await session.execute(
        select(LembreteModel).where(
            and_(
                LembreteModel.id == lembrete_id,
                LembreteModel.usuario_id == usuario.id
            )
        )
    )
    lembrete = result.scalar_one_or_none()
    
    if not lembrete:
        raise HTTPException(404, "Lembrete não encontrado")
    
    lembrete.concluido = True
    await session.commit()
    return {"mensagem": "Lembrete concluído"}


@router.delete("/lembretes/{lembrete_id}")
async def deletar_lembrete(
    lembrete_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Remove um lembrete"""
    result = await session.execute(
        select(LembreteModel).where(
            and_(
                LembreteModel.id == lembrete_id,
                LembreteModel.usuario_id == usuario.id
            )
        )
    )
    lembrete = result.scalar_one_or_none()
    
    if not lembrete:
        raise HTTPException(404, "Lembrete não encontrado")
    
    lembrete.ativo = False
    await session.commit()
    return {"mensagem": "Lembrete removido"}
