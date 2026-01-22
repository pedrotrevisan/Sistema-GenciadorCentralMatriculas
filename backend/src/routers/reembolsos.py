"""Router do Módulo de Reembolsos"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.models import ReembolsoModel

from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/reembolsos", tags=["Reembolsos"])


# Constantes de Motivos de Reembolso
MOTIVOS_REEMBOLSO = {
    "sem_escolaridade": {"label": "Sem Escolaridade", "reter_taxa": False},
    "sem_vaga": {"label": "Sem Vaga 2026.1", "reter_taxa": False},
    "passou_bolsista": {"label": "Passou como Bolsista", "reter_taxa": False},
    "nao_tem_vaga": {"label": "Não Tem Vaga", "reter_taxa": False},
    "desistencia": {"label": "Desistência do Aluno", "reter_taxa": True},
    "outros": {"label": "Outros", "reter_taxa": False}
}

STATUS_REEMBOLSO = {
    "aberto": "Aberto",
    "aguardando_dados_bancarios": "Aguardando Dados Bancários",
    "enviado_financeiro": "Enviado ao Financeiro",
    "pago": "Pago",
    "cancelado": "Cancelado"
}


# DTOs para Reembolsos
class CriarReembolsoDTO(BaseModel):
    aluno_nome: str
    aluno_cpf: Optional[str] = None
    aluno_email: Optional[str] = None
    aluno_telefone: Optional[str] = None
    aluno_menor_idade: Optional[bool] = False
    curso: str
    turma: Optional[str] = None
    motivo: str
    motivo_descricao: Optional[str] = None
    numero_chamado_sgc: Optional[str] = None
    observacoes: Optional[str] = None


class AtualizarReembolsoDTO(BaseModel):
    status: Optional[str] = None
    numero_chamado_sgc: Optional[str] = None
    data_retorno_financeiro: Optional[str] = None
    data_provisao_pagamento: Optional[str] = None
    data_pagamento: Optional[str] = None
    observacoes: Optional[str] = None


class RegistrarDadosBancariosDTO(BaseModel):
    banco_titular_nome: str
    banco_titular_cpf: str
    banco_nome: str
    banco_agencia: str
    banco_operacao: Optional[str] = None
    banco_conta: str
    banco_tipo_conta: str  # corrente ou poupanca
    banco_responsavel_financeiro: Optional[bool] = False


@router.get("/motivos")
async def listar_motivos_reembolso(
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os motivos de reembolso disponíveis"""
    return [
        {
            "value": key,
            "label": config["label"],
            "reter_taxa": config["reter_taxa"]
        }
        for key, config in MOTIVOS_REEMBOLSO.items()
    ]


@router.get("/status")
async def listar_status_reembolso(
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os status de reembolso disponíveis"""
    return [
        {"value": key, "label": label}
        for key, label in STATUS_REEMBOLSO.items()
    ]


@router.get("/dashboard")
async def dashboard_reembolsos(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Dashboard do Módulo de Reembolsos"""
    # Contagem por status
    status_query = await session.execute(
        select(ReembolsoModel.status, func.count(ReembolsoModel.id))
        .group_by(ReembolsoModel.status)
    )
    contagem_status = {row[0]: row[1] for row in status_query.fetchall()}
    
    # Contagem por motivo
    motivo_query = await session.execute(
        select(ReembolsoModel.motivo, func.count(ReembolsoModel.id))
        .group_by(ReembolsoModel.motivo)
    )
    por_motivo = [
        {"motivo": MOTIVOS_REEMBOLSO.get(row[0], {}).get("label", row[0]), "total": row[1]} 
        for row in motivo_query.fetchall()
    ]
    
    # Total geral
    total_query = await session.execute(select(func.count(ReembolsoModel.id)))
    total = total_query.scalar() or 0
    
    # Total em aberto (não pago e não cancelado)
    abertos_query = await session.execute(
        select(func.count(ReembolsoModel.id))
        .where(ReembolsoModel.status.notin_(['pago', 'cancelado']))
    )
    total_abertos = abertos_query.scalar() or 0
    
    return {
        "contagem_status": contagem_status,
        "por_motivo": por_motivo,
        "total": total,
        "total_abertos": total_abertos,
        "total_aberto": contagem_status.get('aberto', 0),
        "total_aguardando": contagem_status.get('aguardando_dados_bancarios', 0),
        "total_enviado": contagem_status.get('enviado_financeiro', 0),
        "total_pago": contagem_status.get('pago', 0),
        "total_cancelado": contagem_status.get('cancelado', 0)
    }


@router.get("/templates-email")
async def listar_templates_email(
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna os templates de email para reembolso"""
    return {
        "solicitacao_dados_bancarios": {
            "assunto": "SENAI CIMATEC - Solicitação de Dados Bancários para Reembolso",
            "corpo": """Olá, boa tarde!

Agradecemos seu contato e esperamos que esteja bem!

Informamos que sua matrícula no curso [NOME_DO_CURSO] foi cancelada devido ao [MOTIVO]. Para prosseguirmos com o reembolso do valor pago, solicitamos, por gentileza, o envio dos seus dados bancários para depósito, conforme os critérios abaixo.

• Candidato maior de 18 anos: informar conta bancária em seu nome;
• Candidato menor de 18 anos: informar conta bancária do responsável financeiro, que deve estar identificado no momento da inscrição.

Dados bancários solicitados:
• Nome completo do titular da conta:
• CPF do titular:
• Banco:
• Agência:
• Conta (com dígito):
• Tipo de conta (corrente/poupança):

Informações importantes:
• O reembolso será realizado exclusivamente para conta corrente ou poupança. Não aceitaremos: conta fácil, conta jurídica, conta salário ou conta conjunta.
• O crédito será realizado em até 15 dias úteis após o recebimento completo das informações.
• O reembolso não será feito via PIX, sendo efetuado apenas por crédito em conta bancária.

Pedimos a gentileza de responder a este e-mail com os dados acima para que possamos dar prosseguimento ao reembolso.

Agradecemos seu interesse no SENAI e nos colocamos à disposição para qualquer dúvida.

[NOME_ATENDENTE]

Central de Atendimento ao Candidato

[EMAIL_ATENDENTE]"""
        },
        "confirmacao_recebimento": {
            "assunto": "SENAI CIMATEC - Confirmação de Recebimento dos Dados Bancários",
            "corpo": """Olá, boa tarde!

Confirmamos o recebimento dos seus dados bancários para reembolso.

Aluno: [NOME_ALUNO]
Curso: [NOME_DO_CURSO]

Informamos que o processo de reembolso foi encaminhado ao setor financeiro. O crédito será realizado em até 15 dias úteis.

Caso tenha alguma dúvida, estamos à disposição.

[NOME_ATENDENTE]

Central de Atendimento ao Candidato

[EMAIL_ATENDENTE]"""
        },
        "confirmacao_pagamento": {
            "assunto": "SENAI CIMATEC - Reembolso Efetuado",
            "corpo": """Olá, boa tarde!

Informamos que o reembolso referente à matrícula no curso [NOME_DO_CURSO] foi efetuado com sucesso.

Aluno: [NOME_ALUNO]
Data do crédito: [DATA_PAGAMENTO]

Por favor, verifique sua conta bancária.

Caso tenha alguma dúvida, estamos à disposição.

[NOME_ATENDENTE]

Central de Atendimento ao Candidato

[EMAIL_ATENDENTE]"""
        }
    }


@router.get("")
async def listar_reembolsos(
    status: Optional[str] = None,
    motivo: Optional[str] = None,
    aluno_nome: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os reembolsos com filtros"""
    query = select(ReembolsoModel)
    
    # Filtros
    if status and status != 'todos':
        query = query.where(ReembolsoModel.status == status)
    if motivo and motivo != 'todos':
        query = query.where(ReembolsoModel.motivo == motivo)
    if aluno_nome:
        query = query.where(ReembolsoModel.aluno_nome.ilike(f'%{aluno_nome}%'))
    
    # Ordenação: mais recentes primeiro
    query = query.order_by(ReembolsoModel.created_at.desc())
    
    # Contagem total
    count_query = select(func.count(ReembolsoModel.id))
    if status and status != 'todos':
        count_query = count_query.where(ReembolsoModel.status == status)
    if motivo and motivo != 'todos':
        count_query = count_query.where(ReembolsoModel.motivo == motivo)
    if aluno_nome:
        count_query = count_query.where(ReembolsoModel.aluno_nome.ilike(f'%{aluno_nome}%'))
    
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginação
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)
    
    result = await session.execute(query)
    reembolsos = result.scalars().all()
    
    return {
        "reembolsos": [
            {
                "id": r.id,
                "aluno_nome": r.aluno_nome,
                "aluno_cpf": r.aluno_cpf,
                "aluno_email": r.aluno_email,
                "aluno_telefone": r.aluno_telefone,
                "aluno_menor_idade": r.aluno_menor_idade,
                "curso": r.curso,
                "turma": r.turma,
                "motivo": r.motivo,
                "motivo_label": MOTIVOS_REEMBOLSO.get(r.motivo, {}).get("label", r.motivo),
                "reter_taxa": r.reter_taxa,
                "numero_chamado_sgc": r.numero_chamado_sgc,
                "status": r.status,
                "status_label": STATUS_REEMBOLSO.get(r.status, r.status),
                "tem_dados_bancarios": r.banco_titular_nome is not None,
                "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
                "data_retorno_financeiro": r.data_retorno_financeiro.isoformat() if r.data_retorno_financeiro else None,
                "data_provisao_pagamento": r.data_provisao_pagamento.isoformat() if r.data_provisao_pagamento else None,
                "data_pagamento": r.data_pagamento.isoformat() if r.data_pagamento else None,
                "observacoes": r.observacoes,
                "criado_por_nome": r.criado_por_nome,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reembolsos
        ],
        "paginacao": {
            "pagina_atual": pagina,
            "por_pagina": por_pagina,
            "total_itens": total,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    }


@router.post("")
async def criar_reembolso(
    dto: CriarReembolsoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria uma nova solicitação de reembolso"""
    # Validar motivo
    if dto.motivo not in MOTIVOS_REEMBOLSO:
        raise HTTPException(status_code=400, detail=f"Motivo inválido. Opções: {', '.join(MOTIVOS_REEMBOLSO.keys())}")
    
    # Determinar se deve reter taxa (10%)
    reter_taxa = MOTIVOS_REEMBOLSO[dto.motivo]["reter_taxa"]
    
    reembolso = ReembolsoModel(
        id=str(uuid.uuid4()),
        aluno_nome=dto.aluno_nome,
        aluno_cpf=dto.aluno_cpf,
        aluno_email=dto.aluno_email,
        aluno_telefone=dto.aluno_telefone,
        aluno_menor_idade=dto.aluno_menor_idade or False,
        curso=dto.curso,
        turma=dto.turma,
        motivo=dto.motivo,
        motivo_descricao=dto.motivo_descricao,
        reter_taxa=reter_taxa,
        numero_chamado_sgc=dto.numero_chamado_sgc,
        status="aberto",
        observacoes=dto.observacoes,
        criado_por_id=usuario.id,
        criado_por_nome=usuario.nome,
        data_abertura=datetime.now(timezone.utc)
    )
    
    session.add(reembolso)
    await session.commit()
    
    return {
        "id": reembolso.id,
        "mensagem": "Reembolso criado com sucesso",
        "status": reembolso.status,
        "reter_taxa": reembolso.reter_taxa
    }


@router.get("/{reembolso_id}")
async def buscar_reembolso(
    reembolso_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Busca detalhes de um reembolso específico"""
    result = await session.execute(
        select(ReembolsoModel).where(ReembolsoModel.id == reembolso_id)
    )
    reembolso = result.scalar_one_or_none()
    
    if not reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    return {
        "id": reembolso.id,
        "aluno_nome": reembolso.aluno_nome,
        "aluno_cpf": reembolso.aluno_cpf,
        "aluno_email": reembolso.aluno_email,
        "aluno_telefone": reembolso.aluno_telefone,
        "aluno_menor_idade": reembolso.aluno_menor_idade,
        "curso": reembolso.curso,
        "turma": reembolso.turma,
        "motivo": reembolso.motivo,
        "motivo_label": MOTIVOS_REEMBOLSO.get(reembolso.motivo, {}).get("label", reembolso.motivo),
        "motivo_descricao": reembolso.motivo_descricao,
        "reter_taxa": reembolso.reter_taxa,
        "numero_chamado_sgc": reembolso.numero_chamado_sgc,
        "status": reembolso.status,
        "status_label": STATUS_REEMBOLSO.get(reembolso.status, reembolso.status),
        # Dados bancários
        "banco_titular_nome": reembolso.banco_titular_nome,
        "banco_titular_cpf": reembolso.banco_titular_cpf,
        "banco_nome": reembolso.banco_nome,
        "banco_agencia": reembolso.banco_agencia,
        "banco_operacao": reembolso.banco_operacao,
        "banco_conta": reembolso.banco_conta,
        "banco_tipo_conta": reembolso.banco_tipo_conta,
        "banco_responsavel_financeiro": reembolso.banco_responsavel_financeiro,
        "dados_bancarios_recebidos_em": reembolso.dados_bancarios_recebidos_em.isoformat() if reembolso.dados_bancarios_recebidos_em else None,
        # Datas
        "data_abertura": reembolso.data_abertura.isoformat() if reembolso.data_abertura else None,
        "data_solicitacao_dados_bancarios": reembolso.data_solicitacao_dados_bancarios.isoformat() if reembolso.data_solicitacao_dados_bancarios else None,
        "data_retorno_financeiro": reembolso.data_retorno_financeiro.isoformat() if reembolso.data_retorno_financeiro else None,
        "data_provisao_pagamento": reembolso.data_provisao_pagamento.isoformat() if reembolso.data_provisao_pagamento else None,
        "data_pagamento": reembolso.data_pagamento.isoformat() if reembolso.data_pagamento else None,
        "observacoes": reembolso.observacoes,
        "criado_por_nome": reembolso.criado_por_nome,
        "atualizado_por_nome": reembolso.atualizado_por_nome,
        "created_at": reembolso.created_at.isoformat() if reembolso.created_at else None,
        "updated_at": reembolso.updated_at.isoformat() if reembolso.updated_at else None
    }


@router.put("/{reembolso_id}")
async def atualizar_reembolso(
    reembolso_id: str,
    dto: AtualizarReembolsoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza um reembolso"""
    result = await session.execute(
        select(ReembolsoModel).where(ReembolsoModel.id == reembolso_id)
    )
    reembolso = result.scalar_one_or_none()
    
    if not reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    # Atualizar campos
    if dto.status:
        if dto.status not in STATUS_REEMBOLSO:
            raise HTTPException(status_code=400, detail=f"Status inválido. Opções: {', '.join(STATUS_REEMBOLSO.keys())}")
        reembolso.status = dto.status
        
        # Se status for "pago", registrar data de pagamento
        if dto.status == "pago" and not reembolso.data_pagamento:
            reembolso.data_pagamento = datetime.now(timezone.utc)
    
    if dto.numero_chamado_sgc:
        reembolso.numero_chamado_sgc = dto.numero_chamado_sgc
    
    if dto.data_retorno_financeiro:
        reembolso.data_retorno_financeiro = datetime.fromisoformat(dto.data_retorno_financeiro.replace('Z', '+00:00'))
    
    if dto.data_provisao_pagamento:
        reembolso.data_provisao_pagamento = datetime.fromisoformat(dto.data_provisao_pagamento.replace('Z', '+00:00'))
    
    if dto.data_pagamento:
        reembolso.data_pagamento = datetime.fromisoformat(dto.data_pagamento.replace('Z', '+00:00'))
    
    if dto.observacoes is not None:
        reembolso.observacoes = dto.observacoes
    
    # Auditoria
    reembolso.atualizado_por_id = usuario.id
    reembolso.atualizado_por_nome = usuario.nome
    reembolso.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    return {
        "id": reembolso.id,
        "mensagem": "Reembolso atualizado com sucesso",
        "status": reembolso.status
    }


@router.delete("/{reembolso_id}")
async def deletar_reembolso(
    reembolso_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Deleta um reembolso (apenas admin)"""
    if usuario.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir reembolsos")
    
    result = await session.execute(
        select(ReembolsoModel).where(ReembolsoModel.id == reembolso_id)
    )
    reembolso = result.scalar_one_or_none()
    
    if not reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    await session.delete(reembolso)
    await session.commit()
    
    return {"mensagem": "Reembolso excluído com sucesso"}


@router.post("/{reembolso_id}/dados-bancarios")
async def registrar_dados_bancarios(
    reembolso_id: str,
    dto: RegistrarDadosBancariosDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Registra os dados bancários para um reembolso"""
    result = await session.execute(
        select(ReembolsoModel).where(ReembolsoModel.id == reembolso_id)
    )
    reembolso = result.scalar_one_or_none()
    
    if not reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    # Atualizar dados bancários
    reembolso.banco_titular_nome = dto.banco_titular_nome
    reembolso.banco_titular_cpf = dto.banco_titular_cpf
    reembolso.banco_nome = dto.banco_nome
    reembolso.banco_agencia = dto.banco_agencia
    reembolso.banco_operacao = dto.banco_operacao
    reembolso.banco_conta = dto.banco_conta
    reembolso.banco_tipo_conta = dto.banco_tipo_conta
    reembolso.banco_responsavel_financeiro = dto.banco_responsavel_financeiro or False
    reembolso.dados_bancarios_recebidos_em = datetime.now(timezone.utc)
    
    # Auditoria
    reembolso.atualizado_por_id = usuario.id
    reembolso.atualizado_por_nome = usuario.nome
    reembolso.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    return {
        "id": reembolso.id,
        "mensagem": "Dados bancários registrados com sucesso",
        "status": reembolso.status
    }


@router.post("/{reembolso_id}/marcar-email-enviado")
async def marcar_email_enviado(
    reembolso_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Marca que o email de solicitação de dados bancários foi enviado"""
    result = await session.execute(
        select(ReembolsoModel).where(ReembolsoModel.id == reembolso_id)
    )
    reembolso = result.scalar_one_or_none()
    
    if not reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    reembolso.data_solicitacao_dados_bancarios = datetime.now(timezone.utc)
    reembolso.status = 'aguardando_dados_bancarios'
    
    # Auditoria
    reembolso.atualizado_por_id = usuario.id
    reembolso.atualizado_por_nome = usuario.nome
    
    await session.commit()
    
    return {
        "id": reembolso.id,
        "mensagem": "Email marcado como enviado",
        "status": reembolso.status
    }
