"""
Router - Módulo de Log de Contatos (Fase 3)

API REST para registro e consulta de interações com alunos.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Usuario
from src.domain.entities_contatos import (
    TipoContatoEnum, ResultadoContatoEnum, MotivoContatoEnum,
    TIPO_CONTATO_LABELS, RESULTADO_CONTATO_LABELS, MOTIVO_CONTATO_LABELS,
    TIPO_CONTATO_COLORS, RESULTADO_CONTATO_COLORS, TIPO_CONTATO_ICONS
)
from src.infrastructure.persistence.repositories_contatos import LogContatoRepository
from src.application.use_cases_contatos import (
    RegistrarContatoUseCase,
    AtualizarContatoUseCase,
    MarcarRetornoRealizadoUseCase,
    ConsultarContatosPedidoUseCase,
    ObterRetornosPendentesUseCase,
    ObterEstatisticasContatosUseCase,
    ExcluirContatoUseCase
)

from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/contatos", tags=["Log de Contatos"])


# ==================== DTOs ====================

class RegistrarContatoDTO(BaseModel):
    pedido_id: str
    tipo: str  # Valor do enum TipoContatoEnum
    resultado: str  # Valor do enum ResultadoContatoEnum
    motivo: str  # Valor do enum MotivoContatoEnum
    descricao: str = Field(..., min_length=5, max_length=2000)
    contato_nome: Optional[str] = Field(None, max_length=200)
    contato_telefone: Optional[str] = Field(None, max_length=20)
    contato_email: Optional[str] = Field(None, max_length=200)
    data_retorno: Optional[datetime] = None


class AtualizarContatoDTO(BaseModel):
    descricao: Optional[str] = Field(None, min_length=5, max_length=2000)
    resultado: Optional[str] = None
    data_retorno: Optional[datetime] = None


# ==================== ENDPOINTS DE REFERÊNCIA ====================

@router.get("/tipos")
async def listar_tipos_contato(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os tipos de contato disponíveis
    """
    return [
        {
            "value": tipo.value,
            "label": TIPO_CONTATO_LABELS.get(tipo, tipo.value),
            "color": TIPO_CONTATO_COLORS.get(tipo, "gray"),
            "icon": TIPO_CONTATO_ICONS.get(tipo, "MoreHorizontal")
        }
        for tipo in TipoContatoEnum
    ]


@router.get("/resultados")
async def listar_resultados_contato(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os resultados de contato disponíveis
    """
    return [
        {
            "value": resultado.value,
            "label": RESULTADO_CONTATO_LABELS.get(resultado, resultado.value),
            "color": RESULTADO_CONTATO_COLORS.get(resultado, "gray")
        }
        for resultado in ResultadoContatoEnum
    ]


@router.get("/motivos")
async def listar_motivos_contato(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os motivos de contato disponíveis
    """
    return [
        {
            "value": motivo.value,
            "label": MOTIVO_CONTATO_LABELS.get(motivo, motivo.value)
        }
        for motivo in MotivoContatoEnum
    ]


# ==================== ENDPOINTS DE ESTATÍSTICAS ====================

@router.get("/stats")
async def obter_estatisticas(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Retorna estatísticas gerais de contatos
    
    Útil para o dashboard de BI
    """
    repo = LogContatoRepository(session)
    use_case = ObterEstatisticasContatosUseCase(repo)
    return await use_case.executar()


@router.get("/retornos")
async def obter_retornos_pendentes(
    limite: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista retornos pendentes e atrasados
    
    Útil para alertas no dashboard
    """
    repo = LogContatoRepository(session)
    use_case = ObterRetornosPendentesUseCase(repo)
    return await use_case.executar(limite)


# ==================== CRUD DE CONTATOS ====================

@router.post("")
async def registrar_contato(
    dto: RegistrarContatoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Registra um novo contato com aluno
    """
    # Validar enums
    try:
        tipo = TipoContatoEnum(dto.tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo de contato inválido: {dto.tipo}")
    
    try:
        resultado = ResultadoContatoEnum(dto.resultado)
    except ValueError:
        raise HTTPException(400, f"Resultado inválido: {dto.resultado}")
    
    try:
        motivo = MotivoContatoEnum(dto.motivo)
    except ValueError:
        raise HTTPException(400, f"Motivo inválido: {dto.motivo}")
    
    repo = LogContatoRepository(session)
    use_case = RegistrarContatoUseCase(repo)
    
    contato = await use_case.executar(
        pedido_id=dto.pedido_id,
        tipo=tipo,
        resultado=resultado,
        motivo=motivo,
        descricao=dto.descricao,
        usuario=usuario,
        contato_nome=dto.contato_nome,
        contato_telefone=dto.contato_telefone,
        contato_email=dto.contato_email,
        data_retorno=dto.data_retorno
    )
    
    await session.commit()
    
    return {
        "id": contato.id,
        "mensagem": "Contato registrado com sucesso",
        "contato": contato.to_dict()
    }


@router.get("/pedido/{pedido_id}")
async def listar_contatos_pedido(
    pedido_id: str,
    tipo: Optional[str] = None,
    resultado: Optional[str] = None,
    limite: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os contatos de um pedido
    
    Retorna resumo e lista de contatos
    """
    tipo_enum = None
    if tipo:
        try:
            tipo_enum = TipoContatoEnum(tipo)
        except ValueError:
            raise HTTPException(400, f"Tipo inválido: {tipo}")
    
    resultado_enum = None
    if resultado:
        try:
            resultado_enum = ResultadoContatoEnum(resultado)
        except ValueError:
            raise HTTPException(400, f"Resultado inválido: {resultado}")
    
    repo = LogContatoRepository(session)
    use_case = ConsultarContatosPedidoUseCase(repo)
    
    return await use_case.executar(pedido_id, tipo_enum, resultado_enum, limite)


@router.get("/{contato_id}")
async def buscar_contato(
    contato_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Busca um contato específico
    """
    repo = LogContatoRepository(session)
    contato = await repo.buscar_por_id(contato_id)
    
    if not contato:
        raise HTTPException(404, "Contato não encontrado")
    
    return contato.to_dict()


@router.put("/{contato_id}")
async def atualizar_contato(
    contato_id: str,
    dto: AtualizarContatoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Atualiza um contato existente
    """
    resultado_enum = None
    if dto.resultado:
        try:
            resultado_enum = ResultadoContatoEnum(dto.resultado)
        except ValueError:
            raise HTTPException(400, f"Resultado inválido: {dto.resultado}")
    
    repo = LogContatoRepository(session)
    use_case = AtualizarContatoUseCase(repo)
    
    try:
        contato = await use_case.executar(
            contato_id=contato_id,
            descricao=dto.descricao,
            resultado=resultado_enum,
            data_retorno=dto.data_retorno
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    
    await session.commit()
    
    return {
        "mensagem": "Contato atualizado",
        "contato": contato.to_dict()
    }


@router.post("/{contato_id}/marcar-retorno")
async def marcar_retorno_realizado(
    contato_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Marca um retorno agendado como realizado
    """
    repo = LogContatoRepository(session)
    use_case = MarcarRetornoRealizadoUseCase(repo)
    
    try:
        contato = await use_case.executar(contato_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    await session.commit()
    
    return {
        "mensagem": "Retorno marcado como realizado",
        "contato": contato.to_dict()
    }


@router.delete("/{contato_id}")
async def excluir_contato(
    contato_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Exclui um contato (apenas admin)
    """
    repo = LogContatoRepository(session)
    use_case = ExcluirContatoUseCase(repo)
    
    try:
        resultado = await use_case.executar(contato_id, usuario)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    
    await session.commit()
    
    return resultado
