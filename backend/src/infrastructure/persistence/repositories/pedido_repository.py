"""Implementação do Repositório de Pedidos com PostgreSQL/SQLAlchemy"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_, extract

from src.domain.repositories import IPedidoRepository
from src.domain.entities import PedidoMatricula, Aluno
from src.domain.value_objects import CPF, Email, Telefone, StatusPedido
from ..models import PedidoModel, AlunoModel


class PedidoRepository(IPedidoRepository):
    """Implementação concreta do repositório de pedidos usando PostgreSQL"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def gerar_numero_protocolo(self) -> str:
        """Gera o próximo número de protocolo no formato CM-YYYY-NNNN"""
        ano_atual = datetime.now().year
        prefixo = f"CM-{ano_atual}-"
        
        # Busca o maior número de protocolo do ano atual
        query = select(func.max(PedidoModel.numero_protocolo)).where(
            PedidoModel.numero_protocolo.like(f"{prefixo}%")
        )
        result = await self.session.execute(query)
        ultimo_protocolo = result.scalar()
        
        if ultimo_protocolo:
            # Extrai o número sequencial do último protocolo
            try:
                ultimo_numero = int(ultimo_protocolo.split("-")[-1])
                proximo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1
        
        return f"{prefixo}{proximo_numero:04d}"

    def _model_to_entity(self, model: PedidoModel) -> PedidoMatricula:
        """Converte model SQLAlchemy para entidade de domínio"""
        alunos = []
        for aluno_model in model.alunos:
            aluno = Aluno(
                id=aluno_model.id,
                nome=aluno_model.nome,
                cpf=CPF(aluno_model.cpf),
                email=Email(aluno_model.email),
                telefone=Telefone(aluno_model.telefone),
                data_nascimento=aluno_model.data_nascimento,
                rg=aluno_model.rg,
                rg_orgao_emissor=aluno_model.rg_orgao_emissor,
                rg_uf=aluno_model.rg_uf,
                endereco_cep=aluno_model.endereco_cep,
                endereco_logradouro=aluno_model.endereco_logradouro,
                endereco_numero=aluno_model.endereco_numero,
                endereco_complemento=aluno_model.endereco_complemento,
                endereco_bairro=aluno_model.endereco_bairro,
                endereco_cidade=aluno_model.endereco_cidade,
                endereco_uf=aluno_model.endereco_uf,
                created_at=aluno_model.created_at,
                updated_at=aluno_model.updated_at
            )
            alunos.append(aluno)

        return PedidoMatricula(
            id=model.id,
            numero_protocolo=model.numero_protocolo,
            consultor_id=model.consultor_id,
            consultor_nome=model.consultor_nome,
            curso_id=model.curso_id,
            curso_nome=model.curso_nome,
            projeto_id=model.projeto_id,
            projeto_nome=model.projeto_nome,
            empresa_id=model.empresa_id,
            empresa_nome=model.empresa_nome,
            alunos=alunos,
            status=StatusPedido.from_string(model.status),
            observacoes=model.observacoes,
            motivo_rejeicao=model.motivo_rejeicao,
            data_exportacao=model.data_exportacao,
            exportado_por=model.exportado_por,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def salvar(self, pedido: PedidoMatricula) -> PedidoMatricula:
        """Salva ou atualiza um pedido"""
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.id == pedido.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.consultor_id = pedido.consultor_id
            existing.consultor_nome = pedido.consultor_nome
            existing.curso_id = pedido.curso_id
            existing.curso_nome = pedido.curso_nome
            existing.projeto_id = pedido.projeto_id
            existing.projeto_nome = pedido.projeto_nome
            existing.empresa_id = pedido.empresa_id
            existing.empresa_nome = pedido.empresa_nome
            existing.status = pedido.status.value
            existing.observacoes = pedido.observacoes
            existing.motivo_rejeicao = pedido.motivo_rejeicao
            existing.data_exportacao = pedido.data_exportacao
            existing.exportado_por = pedido.exportado_por
            existing.updated_at = datetime.now(timezone.utc)

            await self.session.execute(
                delete(AlunoModel).where(AlunoModel.pedido_id == pedido.id)
            )
            
            for aluno in pedido.alunos:
                aluno_model = AlunoModel(
                    id=aluno.id,
                    pedido_id=pedido.id,
                    nome=aluno.nome,
                    cpf=aluno.cpf.valor,
                    email=aluno.email.valor,
                    telefone=aluno.telefone.valor,
                    data_nascimento=aluno.data_nascimento,
                    rg=aluno.rg,
                    rg_orgao_emissor=aluno.rg_orgao_emissor,
                    rg_uf=aluno.rg_uf,
                    endereco_cep=aluno.endereco_cep,
                    endereco_logradouro=aluno.endereco_logradouro,
                    endereco_numero=aluno.endereco_numero,
                    endereco_complemento=aluno.endereco_complemento,
                    endereco_bairro=aluno.endereco_bairro,
                    endereco_cidade=aluno.endereco_cidade,
                    endereco_uf=aluno.endereco_uf
                )
                self.session.add(aluno_model)
        else:
            # Gerar número de protocolo para novo pedido
            numero_protocolo = await self.gerar_numero_protocolo()
            pedido.numero_protocolo = numero_protocolo
            
            pedido_model = PedidoModel(
                id=pedido.id,
                numero_protocolo=numero_protocolo,
                consultor_id=pedido.consultor_id,
                consultor_nome=pedido.consultor_nome,
                curso_id=pedido.curso_id,
                curso_nome=pedido.curso_nome,
                projeto_id=pedido.projeto_id,
                projeto_nome=pedido.projeto_nome,
                empresa_id=pedido.empresa_id,
                empresa_nome=pedido.empresa_nome,
                status=pedido.status.value,
                observacoes=pedido.observacoes,
                motivo_rejeicao=pedido.motivo_rejeicao,
                data_exportacao=pedido.data_exportacao,
                exportado_por=pedido.exportado_por,
                created_at=pedido.created_at,
                updated_at=pedido.updated_at
            )
            self.session.add(pedido_model)

            for aluno in pedido.alunos:
                aluno_model = AlunoModel(
                    id=aluno.id,
                    pedido_id=pedido.id,
                    nome=aluno.nome,
                    cpf=aluno.cpf.valor,
                    email=aluno.email.valor,
                    telefone=aluno.telefone.valor,
                    data_nascimento=aluno.data_nascimento,
                    rg=aluno.rg,
                    rg_orgao_emissor=aluno.rg_orgao_emissor,
                    rg_uf=aluno.rg_uf,
                    endereco_cep=aluno.endereco_cep,
                    endereco_logradouro=aluno.endereco_logradouro,
                    endereco_numero=aluno.endereco_numero,
                    endereco_complemento=aluno.endereco_complemento,
                    endereco_bairro=aluno.endereco_bairro,
                    endereco_cidade=aluno.endereco_cidade,
                    endereco_uf=aluno.endereco_uf
                )
                self.session.add(aluno_model)

        await self.session.commit()
        return pedido

    async def buscar_por_id(self, pedido_id: str) -> Optional[PedidoMatricula]:
        """Busca pedido por ID"""
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.id == pedido_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.refresh(model, ["alunos"])
            return self._model_to_entity(model)
        return None

    async def buscar_por_protocolo(self, numero_protocolo: str) -> Optional[PedidoMatricula]:
        """Busca pedido por número de protocolo"""
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.numero_protocolo == numero_protocolo.upper())
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.refresh(model, ["alunos"])
            return self._model_to_entity(model)
        return None

    async def listar_por_consultor(
        self,
        consultor_id: str,
        status: Optional[StatusPedido] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[PedidoMatricula], int]:
        """Lista pedidos de um consultor com paginação"""
        query = select(PedidoModel).where(PedidoModel.consultor_id == consultor_id)
        count_query = select(func.count(PedidoModel.id)).where(PedidoModel.consultor_id == consultor_id)
        
        if status:
            query = query.where(PedidoModel.status == status.value)
            count_query = count_query.where(PedidoModel.status == status.value)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        offset = (pagina - 1) * por_pagina
        query = query.order_by(PedidoModel.created_at.desc()).offset(offset).limit(por_pagina)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        pedidos = []
        for model in models:
            await self.session.refresh(model, ["alunos"])
            pedidos.append(self._model_to_entity(model))
        
        return pedidos, total

    async def listar_todos(
        self,
        status: Optional[StatusPedido] = None,
        consultor_id: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[PedidoMatricula], int]:
        """Lista todos os pedidos com filtros e paginação"""
        query = select(PedidoModel)
        count_query = select(func.count(PedidoModel.id))
        
        conditions = []
        if status:
            conditions.append(PedidoModel.status == status.value)
        if consultor_id:
            conditions.append(PedidoModel.consultor_id == consultor_id)
        if data_inicio:
            conditions.append(PedidoModel.created_at >= data_inicio)
        if data_fim:
            conditions.append(PedidoModel.created_at <= data_fim)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        offset = (pagina - 1) * por_pagina
        query = query.order_by(PedidoModel.created_at.desc()).offset(offset).limit(por_pagina)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        pedidos = []
        for model in models:
            await self.session.refresh(model, ["alunos"])
            pedidos.append(self._model_to_entity(model))
        
        return pedidos, total

    async def listar_para_exportacao(self) -> List[PedidoMatricula]:
        """Lista pedidos aptos para exportação (status REALIZADO)"""
        query = select(PedidoModel).where(
            PedidoModel.status == StatusPedido.REALIZADO.value
        ).order_by(PedidoModel.created_at.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        pedidos = []
        for model in models:
            await self.session.refresh(model, ["alunos"])
            pedidos.append(self._model_to_entity(model))
        
        return pedidos

    async def existe_por_cpf_curso(
        self,
        cpf: str,
        curso_id: str,
        excluir_pedido_id: Optional[str] = None
    ) -> bool:
        """Verifica se existe pedido com mesmo CPF e curso"""
        query = select(func.count(PedidoModel.id)).join(
            AlunoModel, PedidoModel.id == AlunoModel.pedido_id
        ).where(
            and_(
                PedidoModel.curso_id == curso_id,
                AlunoModel.cpf == cpf,
                PedidoModel.status.notin_([
                    StatusPedido.CANCELADO.value,
                    StatusPedido.REJEITADO.value
                ])
            )
        )
        
        if excluir_pedido_id:
            query = query.where(PedidoModel.id != excluir_pedido_id)
        
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0

    async def buscar_aluno_por_cpf(self, cpf: str) -> Optional[dict]:
        """
        Busca se existe um aluno com o CPF informado em qualquer pedido ativo.
        Retorna informações do aluno existente se encontrado.
        """
        query = select(
            AlunoModel.nome,
            AlunoModel.cpf,
            PedidoModel.id.label('pedido_id'),
            PedidoModel.curso_nome,
            PedidoModel.status
        ).join(
            PedidoModel, AlunoModel.pedido_id == PedidoModel.id
        ).where(
            and_(
                AlunoModel.cpf == cpf,
                PedidoModel.status.notin_([
                    StatusPedido.CANCELADO.value,
                    StatusPedido.REJEITADO.value
                ])
            )
        ).limit(1)
        
        result = await self.session.execute(query)
        row = result.first()
        
        if row:
            return {
                "nome": row.nome,
                "cpf": row.cpf,
                "pedido_id": row.pedido_id,
                "curso_nome": row.curso_nome,
                "status": row.status
            }
        return None

    async def contar_por_status(self, consultor_id: Optional[str] = None) -> dict:
        """Conta pedidos por status"""
        contagem = {status.value: 0 for status in StatusPedido}
        
        query = select(PedidoModel.status, func.count(PedidoModel.id)).group_by(PedidoModel.status)
        
        if consultor_id:
            query = query.where(PedidoModel.consultor_id == consultor_id)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        for status_value, count in rows:
            if status_value in contagem:
                contagem[status_value] = count
        
        contagem["total"] = sum(v for k, v in contagem.items() if k != "total")
        return contagem

    async def deletar(self, pedido_id: str) -> bool:
        """Deleta um pedido"""
        await self.session.execute(
            delete(AlunoModel).where(AlunoModel.pedido_id == pedido_id)
        )
        result = await self.session.execute(
            delete(PedidoModel).where(PedidoModel.id == pedido_id)
        )
        await self.session.commit()
        return result.rowcount > 0
