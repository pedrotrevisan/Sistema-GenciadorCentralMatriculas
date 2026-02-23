"""
Use Case - Criar Pedido com Reserva Automática de Vaga
Versão integrada com sistema de gestão de vagas
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.domain.entities import PedidoMatricula, Aluno, Usuario
from src.domain.value_objects import CPF, Email, Telefone, StatusPedido
from src.domain.repositories import IPedidoRepository, IAuditoriaRepository
from src.domain.exceptions import BusinessRuleException, DuplicidadeException
from src.application.dtos.request import CriarPedidoDTO, AlunoCreateDTO
from src.utils.text_formatters import formatar_nome_proprio, formatar_texto_titulo
from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository
from src.application.use_cases_integracao_vagas import GerenciarReservaPedidoUseCase


class CriarPedidoComReservaUseCase:
    """
    Use Case para criar pedido de matrícula COM reserva automática de vaga
    
    Fluxo:
    1. Valida pedido e alunos
    2. Cria pedido
    3. Se turma_id fornecido -> Reserva vaga automaticamente
    4. Registra auditoria
    """

    def __init__(
        self,
        pedido_repository: IPedidoRepository,
        auditoria_repository: IAuditoriaRepository,
        turma_repository: TurmaRepository,
        reserva_repository: ReservaVagaRepository
    ):
        self.pedido_repository = pedido_repository
        self.auditoria_repository = auditoria_repository
        self.turma_repository = turma_repository
        self.reserva_repository = reserva_repository

    async def executar(self, dto: CriarPedidoDTO, usuario: Usuario, turma_id: Optional[str] = None) -> dict:
        """
        Executa a criação do pedido com reserva de vaga
        
        Args:
            dto: Dados do pedido
            usuario: Usuário criador
            turma_id: ID da turma (opcional)
        
        Returns:
            Dict com pedido e informações da reserva
        """
        
        # Valida que tem pelo menos um aluno
        if not dto.alunos:
            raise BusinessRuleException("Um pedido deve ter pelo menos 1 aluno")

        # Valida vínculo: projeto, empresa ou brasil_mais_produtivo
        vinculo_tipo = dto.vinculo_tipo or ('projeto' if dto.projeto_id else 'empresa')
        
        if vinculo_tipo == 'projeto' and not dto.projeto_id:
            raise BusinessRuleException("Deve informar um Projeto")
        if vinculo_tipo == 'empresa' and not dto.empresa_id:
            raise BusinessRuleException("Deve informar uma Empresa")
        if vinculo_tipo == 'brasil_mais_produtivo' and not dto.empresa_id:
            raise BusinessRuleException("Deve informar a Empresa parceira do Brasil Mais Produtivo")

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
                nome=formatar_nome_proprio(aluno_dto.nome),
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
                endereco_logradouro=formatar_texto_titulo(aluno_dto.endereco_logradouro),
                endereco_numero=aluno_dto.endereco_numero,
                endereco_complemento=aluno_dto.endereco_complemento,
                endereco_bairro=formatar_texto_titulo(aluno_dto.endereco_bairro),
                endereco_cidade=formatar_texto_titulo(aluno_dto.endereco_cidade),
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
            turma_id=turma_id,  # NOVO - vincula turma
            projeto_id=dto.projeto_id,
            projeto_nome=dto.projeto_nome,
            empresa_id=dto.empresa_id,
            empresa_nome=dto.empresa_nome,
            vinculo_tipo=vinculo_tipo,
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
                "empresa": dto.empresa_nome,
                "turma_id": turma_id
            }
        )

        # ========== INTEGRAÇÃO COM SISTEMA DE VAGAS ==========
        reserva = None
        mensagem_reserva = None
        
        if turma_id:
            try:
                # Gerenciar reserva
                gerenciar_reserva_uc = GerenciarReservaPedidoUseCase(
                    self.turma_repository,
                    self.reserva_repository
                )
                
                reserva = await gerenciar_reserva_uc.reservar_vaga_ao_criar_pedido(
                    pedido_id=pedido.id,
                    turma_id=turma_id,
                    usuario_email=usuario.email.value
                )
                
                if reserva:
                    mensagem_reserva = f"✅ Vaga reservada com sucesso! Expira em {reserva.data_expiracao.strftime('%d/%m/%Y')}"
                    
                    # Registrar auditoria da reserva
                    await self.auditoria_repository.registrar(
                        pedido_id=pedido.id,
                        usuario_id=usuario.id,
                        acao="RESERVA_VAGA",
                        detalhes={
                            "turma_id": turma_id,
                            "reserva_id": reserva.id,
                            "data_expiracao": reserva.data_expiracao.isoformat()
                        }
                    )
                else:
                    mensagem_reserva = "⚠️  Pedido criado, mas não foi possível reservar vaga (sem vagas disponíveis ou turma não aberta)"
                    
            except Exception as e:
                # Não bloqueia a criação do pedido se a reserva falhar
                mensagem_reserva = f"⚠️  Pedido criado, mas erro ao reservar vaga: {str(e)}"
                print(f"Erro ao reservar vaga: {str(e)}")

        return {
            "pedido": pedido,
            "reserva": reserva,
            "mensagem_reserva": mensagem_reserva
        }
