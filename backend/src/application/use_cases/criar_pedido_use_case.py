"""Use Case - Criar Pedido de Matrícula"""
import uuid
from datetime import datetime, timezone
from typing import List

from src.domain.entities import PedidoMatricula, Aluno, Usuario
from src.domain.value_objects import CPF, Email, Telefone, StatusPedido
from src.domain.repositories import IPedidoRepository, IAuditoriaRepository
from src.domain.exceptions import BusinessRuleException, DuplicidadeException
from src.application.dtos.request import CriarPedidoDTO, AlunoCreateDTO
from src.utils.text_formatters import formatar_nome_proprio, formatar_texto_titulo


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

        # Verifica CPFs duplicados dentro do mesmo pedido
        cpfs_no_pedido = []
        for aluno_dto in dto.alunos:
            cpf_limpo = CPF._limpar(aluno_dto.cpf)
            if cpf_limpo in cpfs_no_pedido:
                raise DuplicidadeException(
                    f"O CPF {aluno_dto.cpf} está duplicado neste pedido"
                )
            cpfs_no_pedido.append(cpf_limpo)

        # Verifica se algum CPF já existe no sistema (em qualquer pedido ativo)
        for aluno_dto in dto.alunos:
            cpf_limpo = CPF._limpar(aluno_dto.cpf)
            aluno_existente = await self.pedido_repository.buscar_aluno_por_cpf(cpf_limpo)
            
            if aluno_existente:
                nome_existente = aluno_existente['nome']
                curso_existente = aluno_existente['curso_nome']
                raise DuplicidadeException(
                    f"Já existe um aluno cadastrado com o CPF {aluno_dto.cpf}. "
                    f"Nome: {nome_existente}, Curso: {curso_existente}"
                )

        # Cria alunos
        alunos: List[Aluno] = []
        for aluno_dto in dto.alunos:
            aluno = Aluno(
                id=str(uuid.uuid4()),
                nome=formatar_nome_proprio(aluno_dto.nome),  # Formata nome automaticamente
                cpf=CPF(aluno_dto.cpf),
                email=Email(aluno_dto.email),
                telefone=Telefone(aluno_dto.telefone),
                data_nascimento=datetime.fromisoformat(aluno_dto.data_nascimento),
                rg=aluno_dto.rg,
                rg_orgao_emissor=aluno_dto.rg_orgao_emissor.upper() if aluno_dto.rg_orgao_emissor else None,
                rg_uf=aluno_dto.rg_uf.upper(),
                rg_data_emissao=aluno_dto.rg_data_emissao,
                naturalidade=formatar_texto_titulo(aluno_dto.naturalidade) if aluno_dto.naturalidade else None,
                naturalidade_uf=aluno_dto.naturalidade_uf.upper() if aluno_dto.naturalidade_uf else None,
                sexo=aluno_dto.sexo.upper() if aluno_dto.sexo else None,
                cor_raca=aluno_dto.cor_raca,
                grau_instrucao=aluno_dto.grau_instrucao,
                nome_pai=formatar_nome_proprio(aluno_dto.nome_pai) if aluno_dto.nome_pai else None,
                nome_mae=formatar_nome_proprio(aluno_dto.nome_mae) if aluno_dto.nome_mae else None,
                endereco_cep=aluno_dto.endereco_cep,
                endereco_logradouro=formatar_texto_titulo(aluno_dto.endereco_logradouro),  # Formata endereço
                endereco_numero=aluno_dto.endereco_numero,
                endereco_complemento=aluno_dto.endereco_complemento,
                endereco_bairro=formatar_texto_titulo(aluno_dto.endereco_bairro),  # Formata bairro
                endereco_cidade=formatar_texto_titulo(aluno_dto.endereco_cidade),  # Formata cidade
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
