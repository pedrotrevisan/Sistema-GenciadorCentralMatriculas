"""Use Case - Criar Pedido de Matrícula"""
import uuid
from datetime import datetime, timezone
from typing import List

from ...domain.entities import PedidoMatricula, Aluno, Usuario
from ...domain.value_objects import CPF, Email, Telefone, StatusPedido
from ...domain.repositories import IPedidoRepository, IAuditoriaRepository
from ...domain.exceptions import BusinessRuleException, DuplicidadeException
from ..dtos.request import CriarPedidoDTO, AlunoCreateDTO


class CriarPedidoMatriculaUseCase:
    """Use Case para criar pedido de matrícula"""

    def __init__(
        self,
        pedido_repository: IPedidoRepository,
        auditoria_repository: IAuditoriaRepository
    ):
        self.pedido_repository = pedido_repository
        self.auditoria_repository = auditoria_repository

    async def executar(self, dto: CriarPedidoDTO, usuario: Usuario) -> PedidoMatricula:
        """Executa a criação do pedido"""
        
        # Valida que tem pelo menos um aluno
        if not dto.alunos:
            raise BusinessRuleException("Um pedido deve ter pelo menos 1 aluno")

        # Valida projeto OU empresa
        if not dto.projeto_id and not dto.empresa_id:
            raise BusinessRuleException("Deve informar Projeto ou Empresa")
        if dto.projeto_id and dto.empresa_id:
            raise BusinessRuleException("Deve informar apenas Projeto OU Empresa")

        # Verifica duplicidade de CPF no mesmo curso
        for aluno_dto in dto.alunos:
            cpf_limpo = CPF._limpar(aluno_dto.cpf)
            existe = await self.pedido_repository.existe_por_cpf_curso(
                cpf=cpf_limpo,
                curso_id=dto.curso_id
            )
            if existe:
                raise DuplicidadeException(
                    f"Já existe um pedido com o CPF {aluno_dto.cpf} para este curso"
                )

        # Cria alunos
        alunos: List[Aluno] = []
        for aluno_dto in dto.alunos:
            aluno = Aluno(
                id=str(uuid.uuid4()),
                nome=aluno_dto.nome,
                cpf=CPF(aluno_dto.cpf),
                email=Email(aluno_dto.email),
                telefone=Telefone(aluno_dto.telefone),
                data_nascimento=datetime.fromisoformat(aluno_dto.data_nascimento),
                rg=aluno_dto.rg,
                rg_orgao_emissor=aluno_dto.rg_orgao_emissor,
                rg_uf=aluno_dto.rg_uf.upper(),
                endereco_cep=aluno_dto.endereco_cep,
                endereco_logradouro=aluno_dto.endereco_logradouro,
                endereco_numero=aluno_dto.endereco_numero,
                endereco_complemento=aluno_dto.endereco_complemento,
                endereco_bairro=aluno_dto.endereco_bairro,
                endereco_cidade=aluno_dto.endereco_cidade,
                endereco_uf=aluno_dto.endereco_uf.upper()
            )
            alunos.append(aluno)

        # Cria pedido
        pedido = PedidoMatricula(
            id=str(uuid.uuid4()),
            consultor_id=usuario.id,
            consultor_nome=usuario.nome,
            curso_id=dto.curso_id,
            curso_nome=dto.curso_nome,
            projeto_id=dto.projeto_id,
            projeto_nome=dto.projeto_nome,
            empresa_id=dto.empresa_id,
            empresa_nome=dto.empresa_nome,
            alunos=alunos,
            status=StatusPedido.PENDENTE,
            observacoes=dto.observacoes
        )

        # Valida pedido para envio
        pedido.validar_para_envio()

        # Persiste
        pedido = await self.pedido_repository.salvar(pedido)

        # Registra auditoria
        await self.auditoria_repository.registrar(
            pedido_id=pedido.id,
            usuario_id=usuario.id,
            acao="CRIACAO",
            detalhes={
                "curso": dto.curso_nome,
                "total_alunos": len(alunos),
                "projeto": dto.projeto_nome,
                "empresa": dto.empresa_nome
            }
        )

        return pedido
