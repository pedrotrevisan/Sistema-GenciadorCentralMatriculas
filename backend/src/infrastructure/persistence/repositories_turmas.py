"""
Repositórios - Gestão de Turmas e Vagas
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime

from src.domain.entities_turmas import Curso, Turma, ReservaVaga, StatusReserva, StatusTurma
from src.infrastructure.persistence.models_turmas import CursoTurmaModel, TurmaModel, ReservaVagaModel


class CursoRepository:
    """Repositório para operações com Cursos"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, curso: Curso) -> None:
        """Salva ou atualiza um curso"""
        curso_model = CursoTurmaModel(
            id=curso.id,
            nome=curso.nome,
            codigo=curso.codigo,
            carga_horaria=curso.carga_horaria,
            modalidade=curso.modalidade.value,
            descricao=curso.descricao,
            ativo=1 if curso.ativo else 0,
            criado_em=curso.criado_em,
            atualizado_em=datetime.now()
        )
        
        self.session.add(curso_model)
        await self.session.flush()
    
    async def buscar_por_id(self, curso_id: str) -> Optional[Curso]:
        """Busca curso por ID"""
        result = await self.session.execute(
            select(CursoTurmaModel).where(CursoTurmaModel.id == curso_id)
        )
        curso_model = result.scalar_one_or_none()
        
        if not curso_model:
            return None
        
        return self._model_to_entity(curso_model)
    
    async def buscar_por_codigo(self, codigo: str) -> Optional[Curso]:
        """Busca curso por código"""
        result = await self.session.execute(
            select(CursoTurmaModel).where(CursoTurmaModel.codigo == codigo)
        )
        curso_model = result.scalar_one_or_none()
        
        if not curso_model:
            return None
        
        return self._model_to_entity(curso_model)
    
    async def listar_ativos(self) -> List[Curso]:
        """Lista todos os cursos ativos"""
        result = await self.session.execute(
            select(CursoTurmaModel).where(CursoTurmaModel.ativo == 1).order_by(CursoTurmaModel.nome)
        )
        cursos_model = result.scalars().all()
        
        return [self._model_to_entity(c) for c in cursos_model]
    
    async def listar_todos(self) -> List[Curso]:
        """Lista todos os cursos"""
        result = await self.session.execute(
            select(CursoTurmaModel).order_by(CursoTurmaModel.nome)
        )
        cursos_model = result.scalars().all()
        
        return [self._model_to_entity(c) for c in cursos_model]
    
    def _model_to_entity(self, model: CursoTurmaModel) -> Curso:
        """Converte model para entidade"""
        from src.domain.entities_turmas import Modalidade
        
        return Curso(
            id=model.id,
            nome=model.nome,
            codigo=model.codigo,
            carga_horaria=model.carga_horaria,
            modalidade=Modalidade(model.modalidade),
            descricao=model.descricao,
            ativo=bool(model.ativo),
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em
        )


class TurmaRepository:
    """Repositório para operações com Turmas"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, turma: Turma) -> None:
        """Salva ou atualiza uma turma"""
        turma_model = TurmaModel(
            id=turma.id,
            curso_id=turma.curso_id,
            codigo=turma.codigo,
            capacidade_total=turma.capacidade_total,
            vagas_disponiveis=turma.vagas_disponiveis,
            periodo=turma.periodo,
            turno=turma.turno,
            data_inicio=turma.data_inicio,
            data_fim=turma.data_fim,
            status=turma.status.value,
            campus=turma.campus,
            sala=turma.sala,
            criado_em=turma.criado_em,
            atualizado_em=datetime.now()
        )
        
        self.session.add(turma_model)
        await self.session.flush()
    
    async def atualizar_vagas(self, turma_id: str, vagas_disponiveis: int) -> None:
        """Atualiza apenas o contador de vagas disponíveis"""
        result = await self.session.execute(
            select(TurmaModel).where(TurmaModel.id == turma_id)
        )
        turma_model = result.scalar_one_or_none()
        
        if turma_model:
            turma_model.vagas_disponiveis = vagas_disponiveis
            turma_model.atualizado_em = datetime.now()
            await self.session.flush()
    
    async def buscar_por_id(self, turma_id: str) -> Optional[Turma]:
        """Busca turma por ID"""
        result = await self.session.execute(
            select(TurmaModel).where(TurmaModel.id == turma_id)
        )
        turma_model = result.scalar_one_or_none()
        
        if not turma_model:
            return None
        
        return self._model_to_entity(turma_model)
    
    async def buscar_por_codigo(self, codigo: str) -> Optional[Turma]:
        """Busca turma por código"""
        result = await self.session.execute(
            select(TurmaModel).where(TurmaModel.codigo == codigo)
        )
        turma_model = result.scalar_one_or_none()
        
        if not turma_model:
            return None
        
        return self._model_to_entity(turma_model)
    
    async def listar_por_curso(self, curso_id: str) -> List[Turma]:
        """Lista turmas de um curso"""
        result = await self.session.execute(
            select(TurmaModel).where(TurmaModel.curso_id == curso_id).order_by(TurmaModel.periodo.desc())
        )
        turmas_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in turmas_model]
    
    async def listar_abertas(self) -> List[Turma]:
        """Lista turmas abertas para inscrição"""
        result = await self.session.execute(
            select(TurmaModel).where(TurmaModel.status == StatusTurma.ABERTA.value).order_by(TurmaModel.codigo)
        )
        turmas_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in turmas_model]
    
    async def listar_com_vagas(self) -> List[Turma]:
        """Lista turmas que ainda possuem vagas disponíveis"""
        result = await self.session.execute(
            select(TurmaModel).where(
                and_(
                    TurmaModel.status == StatusTurma.ABERTA.value,
                    TurmaModel.vagas_disponiveis > 0
                )
            ).order_by(TurmaModel.codigo)
        )
        turmas_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in turmas_model]
    
    async def obter_estatisticas_ocupacao(self) -> dict:
        """Obtém estatísticas de ocupação de todas as turmas"""
        result = await self.session.execute(
            select(
                func.count(TurmaModel.id).label('total_turmas'),
                func.sum(TurmaModel.capacidade_total).label('capacidade_total'),
                func.sum(TurmaModel.vagas_disponiveis).label('vagas_disponiveis'),
                func.sum(TurmaModel.capacidade_total - TurmaModel.vagas_disponiveis).label('vagas_ocupadas')
            ).where(TurmaModel.status.in_([StatusTurma.ABERTA.value, StatusTurma.EM_ANDAMENTO.value]))
        )
        stats = result.one()
        
        return {
            'total_turmas': stats.total_turmas or 0,
            'capacidade_total': stats.capacidade_total or 0,
            'vagas_disponiveis': stats.vagas_disponiveis or 0,
            'vagas_ocupadas': stats.vagas_ocupadas or 0
        }
    
    def _model_to_entity(self, model: TurmaModel) -> Turma:
        """Converte model para entidade"""
        return Turma(
            id=model.id,
            curso_id=model.curso_id,
            codigo=model.codigo,
            capacidade_total=model.capacidade_total,
            vagas_disponiveis=model.vagas_disponiveis,
            periodo=model.periodo,
            turno=model.turno,
            status=StatusTurma(model.status),
            campus=model.campus,
            sala=model.sala,
            data_inicio=model.data_inicio,
            data_fim=model.data_fim,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em
        )


class ReservaVagaRepository:
    """Repositório para operações com Reservas de Vagas"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, reserva: ReservaVaga) -> None:
        """Salva ou atualiza uma reserva"""
        reserva_model = ReservaVagaModel(
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
        
        self.session.add(reserva_model)
        await self.session.flush()
    
    async def buscar_por_id(self, reserva_id: str) -> Optional[ReservaVaga]:
        """Busca reserva por ID"""
        result = await self.session.execute(
            select(ReservaVagaModel).where(ReservaVagaModel.id == reserva_id)
        )
        reserva_model = result.scalar_one_or_none()
        
        if not reserva_model:
            return None
        
        return self._model_to_entity(reserva_model)
    
    async def buscar_por_pedido(self, pedido_id: str) -> Optional[ReservaVaga]:
        """Busca reserva ativa de um pedido"""
        result = await self.session.execute(
            select(ReservaVagaModel).where(
                and_(
                    ReservaVagaModel.pedido_id == pedido_id,
                    ReservaVagaModel.status.in_([StatusReserva.RESERVADA.value, StatusReserva.CONFIRMADA.value])
                )
            )
        )
        reserva_model = result.scalar_one_or_none()
        
        if not reserva_model:
            return None
        
        return self._model_to_entity(reserva_model)
    
    async def listar_por_turma(self, turma_id: str, status: Optional[StatusReserva] = None) -> List[ReservaVaga]:
        """Lista reservas de uma turma, opcionalmente filtradas por status"""
        query = select(ReservaVagaModel).where(ReservaVagaModel.turma_id == turma_id)
        
        if status:
            query = query.where(ReservaVagaModel.status == status.value)
        
        query = query.order_by(ReservaVagaModel.data_reserva.desc())
        
        result = await self.session.execute(query)
        reservas_model = result.scalars().all()
        
        return [self._model_to_entity(r) for r in reservas_model]
    
    async def listar_expiradas(self) -> List[ReservaVaga]:
        """Lista reservas que expiraram e ainda não foram processadas"""
        agora = datetime.now()
        
        result = await self.session.execute(
            select(ReservaVagaModel).where(
                and_(
                    ReservaVagaModel.status == StatusReserva.RESERVADA.value,
                    ReservaVagaModel.data_expiracao < agora
                )
            )
        )
        reservas_model = result.scalars().all()
        
        return [self._model_to_entity(r) for r in reservas_model]
    
    def _model_to_entity(self, model: ReservaVagaModel) -> ReservaVaga:
        """Converte model para entidade"""
        return ReservaVaga(
            id=model.id,
            turma_id=model.turma_id,
            pedido_id=model.pedido_id,
            status=StatusReserva(model.status),
            data_reserva=model.data_reserva,
            reservado_por=model.reservado_por,
            data_confirmacao=model.data_confirmacao,
            data_liberacao=model.data_liberacao,
            data_expiracao=model.data_expiracao,
            motivo_cancelamento=model.motivo_cancelamento,
            observacoes=model.observacoes
        )
