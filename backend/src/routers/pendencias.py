"""Router do Módulo de Pendências Documentais"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import re
import io

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


class CriarPendenciaManualDTO(BaseModel):
    """DTO para criar pendência manual sem pedido"""
    # Dados do aluno
    aluno_nome: str
    aluno_cpf: str
    aluno_email: Optional[str] = None
    aluno_telefone: Optional[str] = None
    # Documento
    documento_codigo: str
    # Curso (opcional, para contexto)
    curso_nome: Optional[str] = None
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


@router.get("/buscar-aluno/{cpf}")
async def buscar_aluno_por_cpf(
    cpf: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Busca aluno existente pelo CPF"""
    import re
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    result = await session.execute(
        select(AlunoModel, PedidoModel.curso_nome)
        .join(PedidoModel, AlunoModel.pedido_id == PedidoModel.id)
        .where(AlunoModel.cpf == cpf_limpo)
    )
    row = result.first()
    
    if not row:
        return {"encontrado": False, "aluno": None}
    
    aluno, curso_nome = row
    return {
        "encontrado": True,
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "cpf": aluno.cpf,
            "email": aluno.email,
            "telefone": aluno.telefone,
            "curso_nome": curso_nome,
            "pedido_id": aluno.pedido_id
        }
    }


@router.get("/tipos-documento")
async def listar_tipos_documento(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os tipos de documento disponíveis"""
    result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.ativo.is_(True)).order_by(TipoDocumentoModel.codigo)
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
    from datetime import timedelta
    
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
    
    # Total críticas (pendências abertas há mais de 7 dias)
    limite_7_dias = datetime.now(timezone.utc) - timedelta(days=7)
    criticas_query = await session.execute(
        select(func.count(PendenciaModel.id))
        .where(
            and_(
                PendenciaModel.created_at < limite_7_dias,
                PendenciaModel.status.notin_(['aprovado', 'rejeitado'])
            )
        )
    )
    total_criticas = criticas_query.scalar() or 0
    
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
        "total_reenvio": contagem_status.get('reenvio_necessario', 0),
        "total_criticas": total_criticas
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
    # Query base com joins para incluir aluno e pedido (para pegar curso_nome)
    query = (
        select(
            PendenciaModel, 
            AlunoModel.nome.label('aluno_nome'), 
            AlunoModel.cpf.label('aluno_cpf'),
            PedidoModel.curso_nome.label('curso_nome')
        )
        .join(AlunoModel, PendenciaModel.aluno_id == AlunoModel.id)
        .outerjoin(PedidoModel, PendenciaModel.pedido_id == PedidoModel.id)
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
        curso_nome = row[3]
        
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
            "curso_nome": curso_nome or pendencia.observacoes,  # Fallback para observações se for manual
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


@router.post("/manual")
async def criar_pendencia_manual(
    dto: CriarPendenciaManualDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Cria uma nova pendência manual sem necessidade de pedido existente.
    Cria um aluno e pedido temporário para armazenar a pendência.
    """
    import re
    from datetime import datetime, timezone
    
    # Limpar CPF
    cpf_limpo = re.sub(r'\D', '', dto.aluno_cpf)
    if len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido. Deve ter 11 dígitos")
    
    # Buscar tipo de documento
    tipo_doc_result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.codigo == dto.documento_codigo)
    )
    tipo_doc = tipo_doc_result.scalar_one_or_none()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado")
    
    # Verificar se já existe aluno com este CPF
    aluno_existente_result = await session.execute(
        select(AlunoModel).where(AlunoModel.cpf == cpf_limpo)
    )
    aluno = aluno_existente_result.scalar_one_or_none()
    
    if aluno:
        # Aluno já existe - verificar se já tem pendência para este documento
        pendencia_existente_result = await session.execute(
            select(PendenciaModel).where(
                and_(
                    PendenciaModel.aluno_id == aluno.id,
                    PendenciaModel.documento_codigo == dto.documento_codigo,
                    PendenciaModel.status != 'aprovado'
                )
            )
        )
        if pendencia_existente_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409, 
                detail="Já existe uma pendência em aberto para este documento e aluno"
            )
        
        # Usar o pedido existente do aluno
        pedido_id = aluno.pedido_id
    else:
        # Criar novo aluno e pedido manual
        pedido_id = str(uuid.uuid4())
        aluno_id = str(uuid.uuid4())
        
        # Criar pedido manual (sem consultor real, é um pedido administrativo)
        from src.infrastructure.persistence.models import PedidoModel as PM
        
        # Gerar número de protocolo
        count_result = await session.execute(select(func.count(PM.id)))
        count = count_result.scalar() or 0
        ano = datetime.now(timezone.utc).year
        numero_protocolo = f"CM-{ano}-{(count + 1):04d}"
        
        pedido_manual = PM(
            id=pedido_id,
            numero_protocolo=numero_protocolo,
            consultor_id=usuario.id,
            consultor_nome=usuario.nome,
            curso_id="manual",
            curso_nome=dto.curso_nome or "Pendência Manual",
            status="documentacao_pendente",
            observacoes=f"Pedido criado automaticamente para pendência manual - {dto.observacoes or ''}"
        )
        session.add(pedido_manual)
        
        # Criar aluno
        aluno = AlunoModel(
            id=aluno_id,
            pedido_id=pedido_id,
            nome=dto.aluno_nome.strip().title(),
            cpf=cpf_limpo,
            email=dto.aluno_email or "pendencia@manual.com",
            telefone=re.sub(r'\D', '', dto.aluno_telefone or "00000000000"),
            data_nascimento=datetime(2000, 1, 1, tzinfo=timezone.utc),  # Data placeholder
            rg="000000000",
            rg_orgao_emissor="SSP",
            rg_uf="BA",
            endereco_cep="00000000",
            endereco_logradouro="Não informado",
            endereco_numero="0",
            endereco_bairro="Não informado",
            endereco_cidade="Não informado",
            endereco_uf="BA"
        )
        session.add(aluno)
        await session.flush()  # Para garantir que o aluno foi criado antes da pendência
    
    # Criar a pendência
    pendencia = PendenciaModel(
        id=str(uuid.uuid4()),
        aluno_id=aluno.id,
        pedido_id=pedido_id if not aluno.pedido_id else aluno.pedido_id,
        tipo_documento_id=tipo_doc.id,
        documento_codigo=dto.documento_codigo,
        documento_nome=tipo_doc.nome,
        status="pendente",
        observacoes=f"{dto.curso_nome or ''} - {dto.observacoes or ''}".strip(" -"),
        criado_por_id=usuario.id,
        criado_por_nome=usuario.nome
    )
    
    session.add(pendencia)
    await session.commit()
    
    return {
        "id": pendencia.id,
        "mensagem": "Pendência manual criada com sucesso",
        "status": pendencia.status,
        "aluno_id": aluno.id,
        "aluno_nome": dto.aluno_nome,
        "documento": tipo_doc.nome
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


# ==================== IMPORTAÇÃO EM LOTE ====================

class ImportacaoPendenciasResultado(BaseModel):
    sucesso: bool
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    pendencias_criadas: int = 0
    erros: List[dict] = []
    preview: List[dict] = []


def validar_cpf_pendencia(cpf: str) -> tuple:
    """Valida formato do CPF"""
    if not cpf:
        return False, "CPF é obrigatório", ""
    cpf_limpo = re.sub(r'\D', '', str(cpf))
    if len(cpf_limpo) != 11:
        return False, f"CPF deve ter 11 dígitos (encontrado: {len(cpf_limpo)})", ""
    return True, "", cpf_limpo


@router.get("/importacao/template")
async def download_template_pendencias():
    """Gera template Excel para importação de pendências em lote"""
    import pandas as pd
    
    # Criar DataFrame com exemplos
    data = {
        'cpf': ['123.456.789-00', '987.654.321-00', '111.222.333-44'],
        'nome': ['JOÃO CARLOS DA SILVA', 'MARIA EDUARDA DOS SANTOS', 'PEDRO HENRIQUE OLIVEIRA'],
        'email': ['joao.silva@email.com', 'maria.santos@email.com', 'pedro.oliveira@email.com'],
        'telefone': ['(71) 99999-8888', '(71) 98888-7777', '(71) 97777-6666'],
        'curso': ['Técnico em Mecatrônica', 'Técnico em Automação Industrial', 'Engenharia de Produção'],
        'documento_codigo': ['131', '94', '136'],
        'observacoes': ['RG Frente pendente', 'Comprovante de residência', 'Comprovante de escolaridade']
    }
    
    df = pd.DataFrame(data)
    
    # Criar arquivo Excel em memória com duas abas
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendencias')
        
        # Adicionar aba de referência com códigos de documentos
        docs_data = {
            'codigo': ['94', '96', '97', '131', '132', '136', '137', '205'],
            'documento': [
                'Comprovante de Residência',
                'Solicitação Desconto (Sindicato/CIEB/Ex-Aluno)',
                'CPF/RG Responsável Legal (menor de 18 anos)',
                'RG – Frente',
                'RG – Verso',
                'Comprovante de Escolaridade – Frente',
                'Comprovante de Escolaridade – Verso',
                'CPF'
            ],
            'obrigatorio': ['Sim', 'Não', 'Se menor', 'Sim', 'Sim', 'Sim', 'Sim', 'Não']
        }
        df_docs = pd.DataFrame(docs_data)
        df_docs.to_excel(writer, index=False, sheet_name='Codigos_Documentos')
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=template_importacao_pendencias.xlsx"
        }
    )


@router.post("/importacao/validar", response_model=ImportacaoPendenciasResultado)
async def validar_importacao_pendencias(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Valida arquivo de importação de pendências e retorna preview com erros"""
    import pandas as pd
    
    # Validar extensão
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Formato inválido. Use .xlsx, .xls ou .csv")
    
    # Ler arquivo
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(contents), dtype=str, sheet_name=0)
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar nomes das colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Colunas obrigatórias
    colunas_obrigatorias = ['cpf', 'nome', 'documento_codigo']
    colunas_faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
    
    if colunas_faltantes:
        raise HTTPException(400, f"Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}")
    
    # Buscar tipos de documento válidos
    tipos_result = await session.execute(select(TipoDocumentoModel))
    tipos_validos = {t.codigo: t.nome for t in tipos_result.scalars().all()}
    
    # Validar cada linha
    erros = []
    preview = []
    linhas_validas = 0
    
    for idx, row in df.iterrows():
        linha_num = idx + 2  # +2 porque Excel começa em 1 e tem header
        linha_erros = []
        
        # Validar nome
        nome = str(row.get('nome', '')).strip()
        if not nome or len(nome) < 3:
            linha_erros.append("Nome deve ter pelo menos 3 caracteres")
        
        # Validar CPF
        cpf_valido, cpf_erro, cpf_limpo = validar_cpf_pendencia(row.get('cpf', ''))
        if not cpf_valido:
            linha_erros.append(cpf_erro)
        
        # Validar código do documento
        doc_codigo = str(row.get('documento_codigo', '')).strip()
        if not doc_codigo:
            linha_erros.append("Código do documento é obrigatório")
        elif doc_codigo not in tipos_validos:
            linha_erros.append(f"Código de documento inválido: {doc_codigo}. Use: {', '.join(tipos_validos.keys())}")
        
        # Verificar se já existe pendência para este CPF/documento
        if cpf_valido and doc_codigo in tipos_validos:
            aluno_result = await session.execute(
                select(AlunoModel).where(AlunoModel.cpf == cpf_limpo)
            )
            aluno = aluno_result.scalar_one_or_none()
            
            if aluno:
                pendencia_existente = await session.execute(
                    select(PendenciaModel).where(
                        and_(
                            PendenciaModel.aluno_id == aluno.id,
                            PendenciaModel.documento_codigo == doc_codigo,
                            PendenciaModel.status.notin_(['aprovado', 'rejeitado'])
                        )
                    )
                )
                if pendencia_existente.scalar_one_or_none():
                    linha_erros.append("Já existe pendência aberta para este documento")
        
        # Montar preview
        preview_item = {
            "linha": linha_num,
            "nome": nome.title() if nome else "",
            "cpf": cpf_limpo if cpf_valido else str(row.get('cpf', '')),
            "documento_codigo": doc_codigo,
            "documento_nome": tipos_validos.get(doc_codigo, "Desconhecido"),
            "curso": str(row.get('curso', '')).strip(),
            "valido": len(linha_erros) == 0,
            "erros": linha_erros
        }
        preview.append(preview_item)
        
        if linha_erros:
            erros.append({
                "linha": linha_num,
                "erros": linha_erros
            })
        else:
            linhas_validas += 1
    
    return ImportacaoPendenciasResultado(
        sucesso=len(erros) == 0,
        total_linhas=len(df),
        linhas_validas=linhas_validas,
        linhas_com_erro=len(erros),
        erros=erros,
        preview=preview[:100]  # Limitar preview a 100 linhas
    )


@router.post("/importacao/executar")
async def executar_importacao_pendencias(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Executa a importação em lote criando as pendências"""
    import pandas as pd
    
    # Validar extensão
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Formato inválido. Use .xlsx, .xls ou .csv")
    
    # Ler arquivo
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(contents), dtype=str, sheet_name=0)
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar nomes das colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Buscar tipos de documento válidos
    tipos_result = await session.execute(select(TipoDocumentoModel))
    tipos_validos = {t.codigo: t for t in tipos_result.scalars().all()}
    
    pendencias_criadas = 0
    erros = []
    
    for idx, row in df.iterrows():
        linha_num = idx + 2
        
        try:
            # Validar CPF
            cpf_valido, cpf_erro, cpf_limpo = validar_cpf_pendencia(row.get('cpf', ''))
            if not cpf_valido:
                erros.append({"linha": linha_num, "erro": cpf_erro})
                continue
            
            # Validar documento
            doc_codigo = str(row.get('documento_codigo', '')).strip()
            if doc_codigo not in tipos_validos:
                erros.append({"linha": linha_num, "erro": f"Código de documento inválido: {doc_codigo}"})
                continue
            
            tipo_doc = tipos_validos[doc_codigo]
            nome = str(row.get('nome', '')).strip().title()
            email = str(row.get('email', '')).strip().lower() if row.get('email') else "pendencia@importacao.com"
            telefone = re.sub(r'\D', '', str(row.get('telefone', ''))) if row.get('telefone') else "00000000000"
            curso = str(row.get('curso', '')).strip() if row.get('curso') else "Importação em Lote"
            observacoes = str(row.get('observacoes', '')).strip() if row.get('observacoes') else ""
            
            # Verificar se aluno já existe
            aluno_result = await session.execute(
                select(AlunoModel).where(AlunoModel.cpf == cpf_limpo)
            )
            aluno = aluno_result.scalar_one_or_none()
            
            if aluno:
                # Verificar duplicidade de pendência
                pendencia_existente = await session.execute(
                    select(PendenciaModel).where(
                        and_(
                            PendenciaModel.aluno_id == aluno.id,
                            PendenciaModel.documento_codigo == doc_codigo,
                            PendenciaModel.status.notin_(['aprovado', 'rejeitado'])
                        )
                    )
                )
                if pendencia_existente.scalar_one_or_none():
                    erros.append({"linha": linha_num, "erro": "Pendência já existe para este documento"})
                    continue
                
                pedido_id = aluno.pedido_id
            else:
                # Criar novo aluno e pedido
                pedido_id = str(uuid.uuid4())
                aluno_id = str(uuid.uuid4())
                
                # Gerar número de protocolo
                count_result = await session.execute(select(func.count(PedidoModel.id)))
                count = count_result.scalar() or 0
                ano = datetime.now(timezone.utc).year
                numero_protocolo = f"CM-{ano}-{(count + 1):04d}"
                
                pedido = PedidoModel(
                    id=pedido_id,
                    numero_protocolo=numero_protocolo,
                    consultor_id=usuario.id,
                    consultor_nome=usuario.nome,
                    curso_id="importacao",
                    curso_nome=curso,
                    status="documentacao_pendente",
                    observacoes=f"Importação em lote - Linha {linha_num}"
                )
                session.add(pedido)
                
                aluno = AlunoModel(
                    id=aluno_id,
                    pedido_id=pedido_id,
                    nome=nome,
                    cpf=cpf_limpo,
                    email=email,
                    telefone=telefone,
                    data_nascimento=datetime(2000, 1, 1, tzinfo=timezone.utc),
                    rg="000000000",
                    rg_orgao_emissor="SSP",
                    rg_uf="BA",
                    endereco_cep="00000000",
                    endereco_logradouro="Não informado",
                    endereco_numero="0",
                    endereco_bairro="Não informado",
                    endereco_cidade="Não informado",
                    endereco_uf="BA"
                )
                session.add(aluno)
                await session.flush()
            
            # Criar pendência
            pendencia = PendenciaModel(
                id=str(uuid.uuid4()),
                aluno_id=aluno.id,
                pedido_id=pedido_id if not hasattr(aluno, 'pedido_id') or not aluno.pedido_id else aluno.pedido_id,
                tipo_documento_id=tipo_doc.id,
                documento_codigo=doc_codigo,
                documento_nome=tipo_doc.nome,
                status="pendente",
                observacoes=f"{curso} - {observacoes}".strip(" -") if observacoes else curso,
                criado_por_id=usuario.id,
                criado_por_nome=usuario.nome
            )
            session.add(pendencia)
            pendencias_criadas += 1
            
        except Exception as e:
            erros.append({"linha": linha_num, "erro": str(e)})
    
    await session.commit()
    
    return {
        "sucesso": pendencias_criadas > 0,
        "pendencias_criadas": pendencias_criadas,
        "total_linhas": len(df),
        "erros": erros
    }

