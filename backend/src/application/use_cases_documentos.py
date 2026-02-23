"""
Use Cases para Gestão de Pendências Documentais
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.entities_documentos import PendenciaDocumental
from src.domain.entities import Usuario
from src.domain.documentos import (
    TipoDocumentoEnum,
    StatusDocumentoEnum,
    PrioridadeDocumentoEnum,
    DOCUMENTOS_OBRIGATORIOS_PADRAO
)
from src.domain.exceptions import BusinessRuleException, NotFoundException
from src.infrastructure.persistence.repositories_documentos import PendenciaDocumentalRepository


class CriarPendenciaDocumentalUseCase:
    """Use Case: Criar pendência documental"""
    
    def __init__(self, pendencia_repo: PendenciaDocumentalRepository):
        self.pendencia_repo = pendencia_repo
    
    async def executar(
        self,
        pedido_id: str,
        tipo: TipoDocumentoEnum,
        usuario: Usuario,
        obrigatorio: bool = True,
        prioridade: PrioridadeDocumentoEnum = PrioridadeDocumentoEnum.MEDIA,
        prazo_dias: int = 7,
        descricao: Optional[str] = None,
        aluno_id: Optional[str] = None
    ) -> PendenciaDocumental:
        """
        Cria uma nova pendência documental
        
        Args:
            pedido_id: ID do pedido
            tipo: Tipo do documento
            usuario: Usuário criador
            obrigatorio: Se é obrigatório
            prioridade: Prioridade
            prazo_dias: Prazo em dias
            descricao: Descrição adicional
            aluno_id: ID do aluno (opcional)
        """
        pendencia = PendenciaDocumental(
            id=str(uuid4()),
            pedido_id=pedido_id,
            aluno_id=aluno_id,
            tipo=tipo,
            status=StatusDocumentoEnum.PENDENTE,
            prioridade=prioridade,
            obrigatorio=obrigatorio,
            descricao=descricao,
            prazo_limite=datetime.now() + timedelta(days=prazo_dias),
            criado_por_id=usuario.id,
            criado_por_nome=usuario.nome,
            criado_em=datetime.now()
        )
        
        await self.pendencia_repo.salvar(pendencia)
        
        return pendencia


class CriarPendenciasPadraoUseCase:
    """Use Case: Criar pendências padrão para um pedido"""
    
    def __init__(self, pendencia_repo: PendenciaDocumentalRepository):
        self.pendencia_repo = pendencia_repo
    
    async def executar(
        self,
        pedido_id: str,
        usuario: Usuario,
        prazo_dias: int = 7
    ) -> List[PendenciaDocumental]:
        """
        Cria as pendências documentais padrão (obrigatórias)
        """
        pendencias = []
        
        for tipo in DOCUMENTOS_OBRIGATORIOS_PADRAO:
            pendencia = PendenciaDocumental(
                id=str(uuid4()),
                pedido_id=pedido_id,
                tipo=tipo,
                status=StatusDocumentoEnum.PENDENTE,
                prioridade=PrioridadeDocumentoEnum.ALTA,
                obrigatorio=True,
                prazo_limite=datetime.now() + timedelta(days=prazo_dias),
                criado_por_id=usuario.id,
                criado_por_nome=usuario.nome,
                criado_em=datetime.now()
            )
            
            await self.pendencia_repo.salvar(pendencia)
            pendencias.append(pendencia)
        
        return pendencias


class ValidarDocumentoUseCase:
    """Use Case: Aprovar ou recusar documento"""
    
    def __init__(self, pendencia_repo: PendenciaDocumentalRepository):
        self.pendencia_repo = pendencia_repo
    
    async def aprovar(
        self,
        pendencia_id: str,
        usuario: Usuario
    ) -> PendenciaDocumental:
        """Aprova um documento"""
        pendencia = await self.pendencia_repo.buscar_por_id(pendencia_id)
        if not pendencia:
            raise NotFoundException(f"Pendência {pendencia_id} não encontrada")
        
        if not pendencia.foi_enviado():
            raise BusinessRuleException("Apenas documentos enviados podem ser aprovados")
        
        pendencia.aprovar(usuario.id, usuario.nome)
        await self.pendencia_repo.salvar(pendencia)
        
        return pendencia
    
    async def recusar(
        self,
        pendencia_id: str,
        usuario: Usuario,
        motivo: str
    ) -> PendenciaDocumental:
        """Recusa um documento"""
        pendencia = await self.pendencia_repo.buscar_por_id(pendencia_id)
        if not pendencia:
            raise NotFoundException(f"Pendência {pendencia_id} não encontrada")
        
        if not pendencia.foi_enviado():
            raise BusinessRuleException("Apenas documentos enviados podem ser recusados")
        
        if not motivo or len(motivo.strip()) < 10:
            raise BusinessRuleException("Motivo da recusa deve ter pelo menos 10 caracteres")
        
        pendencia.recusar(usuario.id, usuario.nome, motivo)
        await self.pendencia_repo.salvar(pendencia)
        
        return pendencia


class ConsultarPendenciasUseCase:
    """Use Case: Consultar pendências de um pedido"""
    
    def __init__(self, pendencia_repo: PendenciaDocumentalRepository):
        self.pendencia_repo = pendencia_repo
    
    async def executar(
        self,
        pedido_id: str,
        status: Optional[StatusDocumentoEnum] = None
    ) -> dict:
        """
        Retorna checklist de documentos do pedido
        
        Returns:
            Dict com estatísticas e lista de pendências
        """
        pendencias = await self.pendencia_repo.listar_por_pedido(pedido_id, status)
        total_pendentes = await self.pendencia_repo.contar_pendentes_por_pedido(pedido_id)
        
        return {
            'total': len(pendencias),
            'pendentes': total_pendentes,
            'completo': total_pendentes == 0,
            'pendencias': [p.to_dict() for p in pendencias]
        }


class ObterEstatisticasDocumentosUseCase:
    """Use Case: Obter estatísticas para gráficos"""
    
    def __init__(self, pendencia_repo: PendenciaDocumentalRepository):
        self.pendencia_repo = pendencia_repo
    
    async def executar_gerais(self) -> dict:
        """Estatísticas gerais"""
        return await self.pendencia_repo.obter_estatisticas_gerais()
    
    async def executar_por_tipo(self) -> List[dict]:
        """Estatísticas por tipo de documento"""
        return await self.pendencia_repo.obter_estatisticas_por_tipo()
