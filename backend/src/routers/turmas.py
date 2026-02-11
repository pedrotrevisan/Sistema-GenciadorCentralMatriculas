"""
Router - Gestão de Turmas e Vagas
Endpoints para gerenciamento de cursos, turmas e reservas de vagas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories_turmas import CursoRepository, TurmaRepository, ReservaVagaRepository
from src.application.use_cases_turmas import (
    CriarCursoUseCase, CriarTurmaUseCase, ReservarVagaUseCase,
    ConfirmarReservaUseCase, CancelarReservaUseCase,
    ConsultarDisponibilidadeTurmaUseCase, ListarTurmasDisponiveisUseCase,
    ObterEstatisticasGeraisUseCase
)
from src.application.dtos_turmas import *
from src.domain.entities import Usuario, RoleUsuario
from src.domain.exceptions import NotFoundException, BusinessRuleException, ValidationException
from .dependencies import get_current_user

router = APIRouter(prefix="/turmas", tags=["Gestão de Turmas e Vagas"])


# ========== ENDPOINTS DE CURSOS ==========

@router.post("/cursos", response_model=CursoResponseDTO, status_code=status.HTTP_201_CREATED)
async def criar_curso(
    dto: CriarCursoDTO,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🎓 **Criar novo curso**
    
    Apenas administradores podem criar cursos.
    """
    # Verificar permissão
    if usuario.role != RoleUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar cursos")
    
    try:
        use_case = CriarCursoUseCase(CursoRepository(session))
        curso = await use_case.execute(
            nome=dto.nome,
            codigo=dto.codigo,
            carga_horaria=dto.carga_horaria,
            modalidade=dto.modalidade,
            descricao=dto.descricao
        )
        
        await session.commit()
        
        return CursoResponseDTO(
            id=curso.id,
            nome=curso.nome,
            codigo=curso.codigo,
            carga_horaria=curso.carga_horaria,
            modalidade=curso.modalidade.value,
            descricao=curso.descricao,
            ativo=curso.ativo,
            criado_em=curso.criado_em,
            atualizado_em=curso.atualizado_em
        )
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar curso: {str(e)}")


@router.get("/cursos", response_model=ListaCursosResponseDTO)
async def listar_cursos(
    apenas_ativos: bool = True,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """📚 **Listar cursos**"""
    try:
        curso_repo = CursoRepository(session)
        
        if apenas_ativos:
            cursos = await curso_repo.listar_ativos()
        else:
            cursos = await curso_repo.listar_todos()
        
        cursos_dto = [
            CursoResponseDTO(
                id=c.id,
                nome=c.nome,
                codigo=c.codigo,
                carga_horaria=c.carga_horaria,
                modalidade=c.modalidade.value,
                descricao=c.descricao,
                ativo=c.ativo,
                criado_em=c.criado_em,
                atualizado_em=c.atualizado_em
            )
            for c in cursos
        ]
        
        return ListaCursosResponseDTO(total=len(cursos_dto), cursos=cursos_dto)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar cursos: {str(e)}")


@router.get("/cursos/{curso_id}", response_model=CursoResponseDTO)
async def buscar_curso(
    curso_id: str,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """🔍 **Buscar curso por ID**"""
    try:
        curso_repo = CursoRepository(session)
        curso = await curso_repo.buscar_por_id(curso_id)
        
        if not curso:
            raise HTTPException(status_code=404, detail="Curso não encontrado")
        
        return CursoResponseDTO(
            id=curso.id,
            nome=curso.nome,
            codigo=curso.codigo,
            carga_horaria=curso.carga_horaria,
            modalidade=curso.modalidade.value,
            descricao=curso.descricao,
            ativo=curso.ativo,
            criado_em=curso.criado_em,
            atualizado_em=curso.atualizado_em
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar curso: {str(e)}")


# ========== ENDPOINTS DE TURMAS ==========

@router.post("/criar-turma", response_model=TurmaResponseDTO, status_code=status.HTTP_201_CREATED)
async def criar_turma(
    dto: CriarTurmaDTO,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🏫 **Criar nova turma**
    
    Cria uma turma com capacidade definida e vagas disponíveis.
    Apenas administradores podem criar turmas.
    """
    # Verificar permissão
    if usuario.role != RoleUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar turmas")
    
    try:
        use_case = CriarTurmaUseCase(
            TurmaRepository(session),
            CursoRepository(session)
        )
        
        turma = await use_case.execute(
            curso_id=dto.curso_id,
            codigo=dto.codigo,
            capacidade_total=dto.capacidade_total,
            periodo=dto.periodo,
            turno=dto.turno,
            campus=dto.campus,
            sala=dto.sala,
            data_inicio=dto.data_inicio,
            data_fim=dto.data_fim
        )
        
        await session.commit()
        
        return TurmaResponseDTO(
            id=turma.id,
            curso_id=turma.curso_id,
            codigo=turma.codigo,
            capacidade_total=turma.capacidade_total,
            vagas_disponiveis=turma.vagas_disponiveis,
            vagas_ocupadas=turma.capacidade_total - turma.vagas_disponiveis,
            ocupacao_percentual=turma.calcular_ocupacao_percentual(),
            periodo=turma.periodo,
            turno=turma.turno,
            status=turma.status.value,
            campus=turma.campus,
            sala=turma.sala,
            data_inicio=turma.data_inicio,
            data_fim=turma.data_fim,
            esta_lotada=turma.esta_lotada(),
            esta_quase_lotada=turma.esta_quase_lotada(),
            criado_em=turma.criado_em
        )
    
    except (NotFoundException, ValidationException, BusinessRuleException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar turma: {str(e)}")


@router.get("/disponiveis", response_model=ListaTurmasDisponiveisResponseDTO)
async def listar_turmas_disponiveis(
    curso_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    📊 **Listar turmas com vagas disponíveis**
    
    Retorna apenas turmas abertas que ainda possuem vagas.
    Útil para seleção de turma ao criar matrícula.
    """
    try:
        use_case = ListarTurmasDisponiveisUseCase(
            TurmaRepository(session),
            CursoRepository(session)
        )
        
        turmas = await use_case.execute(curso_id=curso_id)
        
        return ListaTurmasDisponiveisResponseDTO(
            total=len(turmas),
            turmas=[TurmaDisponivelDTO(**t) for t in turmas]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar turmas: {str(e)}")


@router.get("/{turma_id}/disponibilidade", response_model=DisponibilidadeResponseDTO)
async def consultar_disponibilidade(
    turma_id: str,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🔍 **Consultar disponibilidade de turma**
    
    Retorna informações detalhadas sobre ocupação e disponibilidade.
    """
    try:
        use_case = ConsultarDisponibilidadeTurmaUseCase(TurmaRepository(session))
        resultado = await use_case.execute(turma_id)
        
        return DisponibilidadeResponseDTO(**resultado)
    
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar disponibilidade: {str(e)}")


@router.get("/estatisticas/geral", response_model=EstatisticasGeraisResponseDTO)
async def obter_estatisticas_gerais(
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    📈 **Estatísticas gerais do sistema de vagas**
    
    Retorna visão consolidada de ocupação de todas as turmas.
    """
    try:
        use_case = ObterEstatisticasGeraisUseCase(TurmaRepository(session))
        stats = await use_case.execute()
        
        return EstatisticasGeraisResponseDTO(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


# ========== ENDPOINTS DE RESERVAS ==========

@router.post("/reservar-vaga", response_model=ReservaVagaResponseDTO, status_code=status.HTTP_201_CREATED)
async def reservar_vaga(
    dto: ReservarVagaDTO,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    🎫 **Reservar vaga em turma**
    
    Reserva temporariamente uma vaga para um pedido de matrícula.
    A reserva expira se não for confirmada dentro do prazo.
    """
    try:
        use_case = ReservarVagaUseCase(
            TurmaRepository(session),
            ReservaVagaRepository(session)
        )
        
        reserva = await use_case.execute(
            turma_id=dto.turma_id,
            pedido_id=dto.pedido_id,
            reservado_por=usuario.email.value,
            dias_expiracao=dto.dias_expiracao
        )
        
        await session.commit()
        
        return ReservaVagaResponseDTO(
            id=reserva.id,
            turma_id=reserva.turma_id,
            pedido_id=reserva.pedido_id,
            status=reserva.status.value,
            data_reserva=reserva.data_reserva,
            data_confirmacao=reserva.data_confirmacao,
            data_liberacao=reserva.data_liberacao,
            data_expiracao=reserva.data_expiracao,
            reservado_por=reserva.reservado_por,
            motivo_cancelamento=reserva.motivo_cancelamento,
            observacoes=reserva.observacoes
        )
    
    except (NotFoundException, BusinessRuleException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao reservar vaga: {str(e)}")


@router.post("/reservas/{reserva_id}/confirmar", response_model=ReservaVagaResponseDTO)
async def confirmar_reserva(
    reserva_id: str,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    ✅ **Confirmar reserva de vaga**
    
    Confirma a reserva quando o aluno é oficialmente matriculado.
    """
    try:
        use_case = ConfirmarReservaUseCase(ReservaVagaRepository(session))
        reserva = await use_case.execute(reserva_id)
        
        await session.commit()
        
        return ReservaVagaResponseDTO(
            id=reserva.id,
            turma_id=reserva.turma_id,
            pedido_id=reserva.pedido_id,
            status=reserva.status.value,
            data_reserva=reserva.data_reserva,
            data_confirmacao=reserva.data_confirmacao,
            data_liberacao=reserva.data_liberacao,
            data_expiracao=reserva.data_expiracao,
            reservado_por=reserva.reservado_por,
            motivo_cancelamento=reserva.motivo_cancelamento,
            observacoes=reserva.observacoes
        )
    
    except (NotFoundException, BusinessRuleException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao confirmar reserva: {str(e)}")


@router.post("/reservas/{reserva_id}/cancelar", response_model=ReservaVagaResponseDTO)
async def cancelar_reserva(
    reserva_id: str,
    dto: CancelarReservaDTO,
    session: AsyncSession = Depends(get_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    ❌ **Cancelar reserva e liberar vaga**
    
    Cancela a reserva e libera a vaga para outros alunos.
    """
    try:
        use_case = CancelarReservaUseCase(
            ReservaVagaRepository(session),
            TurmaRepository(session)
        )
        
        reserva = await use_case.execute(reserva_id, dto.motivo)
        
        await session.commit()
        
        return ReservaVagaResponseDTO(
            id=reserva.id,
            turma_id=reserva.turma_id,
            pedido_id=reserva.pedido_id,
            status=reserva.status.value,
            data_reserva=reserva.data_reserva,
            data_confirmacao=reserva.data_confirmacao,
            data_liberacao=reserva.data_liberacao,
            data_expiracao=reserva.data_expiracao,
            reservado_por=reserva.reservado_por,
            motivo_cancelamento=reserva.motivo_cancelamento,
            observacoes=reserva.observacoes
        )
    
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar reserva: {str(e)}")
