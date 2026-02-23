"""
Router - Máquina de Estados de Matrícula
Endpoints para gerenciar transições de status com validação e histórico
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories_transicoes import TransicaoStatusRepository
from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository
from src.infrastructure.persistence.repositories import PedidoRepository
from src.application.use_cases_transicoes import (
    TransicionarStatusUseCase,
    ConsultarHistoricoStatusUseCase,
    ObterProximosStatusUseCase
)
from src.application.dtos_transicoes import *
from src.domain.status_matricula import StatusMatriculaEnum, STATUS_LABELS, STATUS_COLORS
from src.domain.entities import Usuario
from src.domain.exceptions import NotFoundException, BusinessRuleException
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/status", tags=["Máquina de Estados"])


@router.get("/enums", response_model=dict)
async def listar_status_enums():
    """
    📋 **Lista todos os status disponíveis**
    
    Retorna enum completo com labels e cores para UI
    """
    return {
        "status": [
            {
                "valor": s.value,
                "label": STATUS_LABELS[s],
                "cor": STATUS_COLORS[s]
            }
            for s in StatusMatriculaEnum
        ]
    }


@router.get("/pedidos/{pedido_id}/proximos", response_model=ProximosStatusResponseDTO)
async def obter_proximos_status(
    pedido_id: str,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🔍 **Consultar próximos status válidos**
    
    Retorna quais transições são permitidas a partir do status atual do pedido.
    Útil para popular dropdowns na UI.
    """
    try:
        pedido_repo = PedidoRepository(session)
        use_case = ObterProximosStatusUseCase(pedido_repo)
        
        resultado = await use_case.executar(pedido_id)
        
        return ProximosStatusResponseDTO(
            status_atual=StatusDisponivelDTO(**resultado["status_atual"]),
            proximos_status=[StatusDisponivelDTO(**s) for s in resultado["proximos_status"]]
        )
    
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar próximos status: {str(e)}")


@router.post("/pedidos/{pedido_id}/transicionar", response_model=TransicaoStatusResponseDTO, status_code=status.HTTP_201_CREATED)
async def transicionar_status(
    pedido_id: str,
    dto: TransicionarStatusDTO,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🔄 **Transicionar status do pedido**
    
    Muda o status do pedido com validação automática de fluxo.
    
    **Validações:**
    - Transição deve ser permitida pelo fluxo
    - Motivo obrigatório para cancelamento
    - Histórico registrado automaticamente
    
    **Ações Automáticas:**
    - Matriculado → Confirma reserva de vaga
    - Cancelado/Trancado → Libera vaga
    """
    try:
        # Validar status
        try:
            status_novo = StatusMatriculaEnum(dto.status_novo)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Status inválido: {dto.status_novo}. Use /status/enums para ver opções válidas"
            )
        
        # Executar transição
        pedido_repo = PedidoRepository(session)
        transicao_repo = TransicaoStatusRepository(session)
        turma_repo = TurmaRepository(session)
        reserva_repo = ReservaVagaRepository(session)
        
        use_case = TransicionarStatusUseCase(
            pedido_repo, transicao_repo, turma_repo, reserva_repo
        )
        
        transicao = await use_case.executar(
            pedido_id=pedido_id,
            status_novo=status_novo,
            usuario=usuario,
            motivo=dto.motivo,
            observacoes=dto.observacoes
        )
        
        await session.commit()
        
        return TransicaoStatusResponseDTO(
            id=transicao.id,
            pedido_id=transicao.pedido_id,
            status_anterior=transicao.status_anterior.value,
            status_novo=transicao.status_novo.value,
            tipo_transicao=transicao.tipo_transicao.value,
            data_transicao=transicao.data_transicao,
            motivo=transicao.motivo,
            observacoes=transicao.observacoes,
            usuario_id=transicao.usuario_id,
            usuario_nome=transicao.usuario_nome,
            usuario_email=transicao.usuario_email
        )
    
    except (NotFoundException, BusinessRuleException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao transicionar status: {str(e)}")


@router.get("/pedidos/{pedido_id}/historico", response_model=HistoricoStatusResponseDTO)
async def consultar_historico_status(
    pedido_id: str,
    limite: int = 50,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    📜 **Consultar histórico de transições**
    
    Retorna timeline completa de mudanças de status do pedido.
    
    **Informações incluídas:**
    - Status anterior e novo
    - Data e hora da mudança
    - Usuário responsável
    - Motivo e observações
    """
    try:
        transicao_repo = TransicaoStatusRepository(session)
        use_case = ConsultarHistoricoStatusUseCase(transicao_repo)
        
        transicoes = await use_case.executar(pedido_id, limite)
        
        transicoes_dto = [
            TransicaoStatusResponseDTO(
                id=t.id,
                pedido_id=t.pedido_id,
                status_anterior=t.status_anterior.value,
                status_novo=t.status_novo.value,
                tipo_transicao=t.tipo_transicao.value,
                data_transicao=t.data_transicao,
                motivo=t.motivo,
                observacoes=t.observacoes,
                usuario_id=t.usuario_id,
                usuario_nome=t.usuario_nome,
                usuario_email=t.usuario_email
            )
            for t in transicoes
        ]
        
        return HistoricoStatusResponseDTO(
            total=len(transicoes_dto),
            transicoes=transicoes_dto
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar histórico: {str(e)}")
