"""
Use Cases - Módulo de Log de Contatos (Fase 3)
"""
import uuid
from datetime import datetime
from typing import List, Optional

from src.domain.entities import Usuario
from src.domain.entities_contatos import (
    ContatoEntity,
    TipoContatoEnum,
    ResultadoContatoEnum,
    MotivoContatoEnum
)
from src.infrastructure.persistence.repositories_contatos import LogContatoRepository


class RegistrarContatoUseCase:
    """Use Case: Registrar um novo contato com aluno"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(
        self,
        pedido_id: str,
        tipo: TipoContatoEnum,
        resultado: ResultadoContatoEnum,
        motivo: MotivoContatoEnum,
        descricao: str,
        usuario: Usuario,
        contato_nome: Optional[str] = None,
        contato_telefone: Optional[str] = None,
        contato_email: Optional[str] = None,
        data_retorno: Optional[datetime] = None
    ) -> ContatoEntity:
        """
        Registra um novo contato
        
        Args:
            pedido_id: ID do pedido relacionado
            tipo: Tipo de contato (ligação, WhatsApp, etc.)
            resultado: Resultado do contato
            motivo: Motivo/assunto do contato
            descricao: Descrição detalhada
            usuario: Usuário que está registrando
            contato_nome: Nome de quem atendeu (se diferente do aluno)
            contato_telefone: Telefone usado
            contato_email: Email usado
            data_retorno: Data para retornar (se aplicável)
        """
        entity = ContatoEntity(
            id=str(uuid.uuid4()),
            pedido_id=pedido_id,
            tipo=tipo,
            resultado=resultado,
            motivo=motivo,
            descricao=descricao.strip(),
            contato_nome=contato_nome.strip() if contato_nome else None,
            contato_telefone=contato_telefone,
            contato_email=contato_email,
            data_retorno=data_retorno,
            retorno_realizado=False,
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            criado_em=datetime.now()
        )
        
        return await self.repository.salvar(entity)


class AtualizarContatoUseCase:
    """Use Case: Atualizar um contato existente"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(
        self,
        contato_id: str,
        descricao: Optional[str] = None,
        resultado: Optional[ResultadoContatoEnum] = None,
        data_retorno: Optional[datetime] = None
    ) -> ContatoEntity:
        """Atualiza campos de um contato"""
        entity = await self.repository.buscar_por_id(contato_id)
        
        if not entity:
            raise ValueError("Contato não encontrado")
        
        if descricao:
            entity.descricao = descricao.strip()
        if resultado:
            entity.resultado = resultado
        if data_retorno:
            entity.data_retorno = data_retorno
            entity.retorno_realizado = False
        
        entity.atualizado_em = datetime.now()
        
        return await self.repository.salvar(entity)


class MarcarRetornoRealizadoUseCase:
    """Use Case: Marcar retorno como realizado"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(self, contato_id: str) -> ContatoEntity:
        """Marca o retorno agendado como realizado"""
        entity = await self.repository.buscar_por_id(contato_id)
        
        if not entity:
            raise ValueError("Contato não encontrado")
        
        if not entity.data_retorno:
            raise ValueError("Este contato não tem retorno agendado")
        
        entity.marcar_retorno_realizado()
        
        return await self.repository.salvar(entity)


class ConsultarContatosPedidoUseCase:
    """Use Case: Consultar contatos de um pedido"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(
        self,
        pedido_id: str,
        tipo: Optional[TipoContatoEnum] = None,
        resultado: Optional[ResultadoContatoEnum] = None,
        limite: int = 50
    ) -> dict:
        """
        Consulta contatos de um pedido com resumo
        
        Returns:
            Dict com resumo e lista de contatos
        """
        contatos = await self.repository.listar_por_pedido(
            pedido_id, tipo, resultado, limite
        )
        resumo = await self.repository.obter_resumo_pedido(pedido_id)
        
        return {
            "resumo": resumo.to_dict(),
            "contatos": [c.to_dict() for c in contatos]
        }


class ObterRetornosPendentesUseCase:
    """Use Case: Listar retornos pendentes"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(self, limite: int = 50) -> dict:
        """Lista todos os retornos pendentes"""
        pendentes = await self.repository.listar_retornos_pendentes(limite)
        atrasados = await self.repository.listar_retornos_atrasados()
        
        return {
            "pendentes": [c.to_dict() for c in pendentes],
            "atrasados": [c.to_dict() for c in atrasados],
            "total_pendentes": len(pendentes),
            "total_atrasados": len(atrasados)
        }


class ObterEstatisticasContatosUseCase:
    """Use Case: Obter estatísticas de contatos"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(self) -> dict:
        """Retorna estatísticas gerais de contatos"""
        return await self.repository.obter_estatisticas_gerais()


class ExcluirContatoUseCase:
    """Use Case: Excluir um contato"""
    
    def __init__(self, repository: LogContatoRepository):
        self.repository = repository
    
    async def executar(self, contato_id: str, usuario: Usuario) -> dict:
        """
        Exclui um contato (apenas admin)
        
        Args:
            contato_id: ID do contato
            usuario: Usuário que está excluindo (deve ser admin)
        """
        if usuario.role != 'admin':
            raise PermissionError("Apenas administradores podem excluir contatos")
        
        entity = await self.repository.buscar_por_id(contato_id)
        if not entity:
            raise ValueError("Contato não encontrado")
        
        await self.repository.excluir(contato_id)
        
        return {"mensagem": "Contato excluído com sucesso"}
