"""Serviço de Fluxo de Cancelamento - Conforme procedimento CAC SENAI"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==================== TIPOS DE CANCELAMENTO ====================

class TipoCancelamento(Enum):
    """Tipos de cancelamento conforme e-mail CAC"""
    SOLICITADO_CANDIDATO = "solicitado_candidato"  # Solicitado pelo próprio candidato
    SENAI = "senai"  # Realizado pelo SENAI (falta de documentos, não atende requisito, etc)
    PRAZO_EXPIRADO = "prazo_expirado"  # Automático - prazo de 5 dias expirado
    NAO_ATENDE_REQUISITO = "nao_atende_requisito"  # Não atende pré-requisitos do curso


class StatusCancelamento(Enum):
    """Status do processo de cancelamento"""
    SOLICITADO = "solicitado"  # Solicitação recebida
    AGUARDANDO_NRM = "aguardando_nrm"  # Aguardando tentativa de reversão pelo NRM (48h)
    NRM_TENTOU_REVERSAO = "nrm_tentou_reversao"  # NRM tentou reverter
    CONFIRMADO = "confirmado"  # Candidato confirmou cancelamento
    AGUARDANDO_DADOS_BANCARIOS = "aguardando_dados_bancarios"  # Esperando dados para reembolso
    CHAMADO_FINANCEIRO = "chamado_financeiro"  # Chamado aberto para financeiro
    FINALIZADO = "finalizado"  # Cancelamento concluído


# ==================== RESPONSABILIDADES POR STATUS ====================

RESPONSABILIDADE_CANCELAMENTO = {
    # Status → Responsável pelo próximo passo
    "pre_analise": "CAC",  # CAC solicita dados bancários e abre chamado financeiro
    "analise_documental": "CAC",  # CAC solicita dados bancários e abre chamado financeiro
    "matriculado": "CAA",  # CAA orienta candidato a abrir requerimento via Portal do Aluno
    "realizado": "CAA",  # CAA orienta candidato
    "aguardando_pagamento": "CAC",  # CAC processa cancelamento
    "aprovado": "CAC",  # CAC processa cancelamento
}

PRAZO_NRM_HORAS = 48  # 48 horas para NRM tentar reverter


# ==================== DOCUMENTOS TOTVS ====================

DOCUMENTOS_ESCOLARIDADE_TOTVS = {
    "136": {
        "codigo": "136",
        "nome": "Escolaridade - Tipo 1",
        "descricao": "Documento de escolaridade geral",
        "validacao": "VALIDADO"
    },
    "137": {
        "codigo": "137",
        "nome": "Escolaridade - Tipo 2",
        "descricao": "Documento de escolaridade complementar",
        "validacao": "VALIDADO"
    },
    "93": {
        "codigo": "93",
        "nome": "Data de Entrega",
        "descricao": "Registro de data de entrega de documento",
        "validacao": "VALIDADO + data entrega"
    },
    "182": {
        "codigo": "182",
        "nome": "Histórico Escolar - Ensino Médio",
        "descricao": "Histórico escolar completo do ensino médio",
        "validacao": "VALIDADO",
        "quando_incluir": "Quando aluno entrega Histórico Escolar"
    },
    "165": {
        "codigo": "165",
        "nome": "Atestado de Conclusão do Ensino Médio",
        "descricao": "Atestado de conclusão (deve ser atualizado com data de 2025)",
        "validacao": "VALIDADO",
        "quando_incluir": "Quando aluno entrega apenas Atestado de Conclusão (sem Histórico)"
    }
}

# Fluxo de validação de documentos de escolaridade
FLUXO_VALIDACAO_ESCOLARIDADE = {
    "historico_escolar": {
        "documentos_validar": ["136", "137", "93"],
        "documentos_incluir": ["182"],
        "status_final": "MAC",  # Matrícula Confirmada
        "descricao": "Histórico Escolar - valida 136, 137, 93 e inclui 182"
    },
    "atestado_matricula": {
        "documentos_validar": ["136", "137", "93"],
        "documentos_incluir": [],  # Não precisa incluir nenhum documento adicional
        "status_final": "MAC",
        "descricao": "Atestado/Comprovante de Matrícula - cursando a partir do 2º ano EM"
    },
    "atestado_conclusao": {
        "documentos_validar": ["136", "137", "93"],
        "documentos_incluir": ["165"],
        "status_final": "MAC",
        "descricao": "Atestado de Conclusão (sem Histórico) - deve ser atualizado com data de 2025"
    }
}


# ==================== SERVIÇO DE CANCELAMENTO ====================

class CancelamentoService:
    """Serviço para gerenciar fluxo de cancelamento"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def solicitar_cancelamento(
        self,
        pedido_id: str,
        tipo: TipoCancelamento,
        motivo: str,
        solicitante_id: str,
        solicitante_nome: str
    ) -> Dict[str, Any]:
        """
        Inicia processo de cancelamento de matrícula.
        Se solicitado pelo candidato, encaminha para NRM (48h para reverter).
        """
        from src.infrastructure.persistence.models import PedidoModel
        
        # Buscar pedido
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.id == pedido_id)
        )
        pedido = result.scalar_one_or_none()
        
        if not pedido:
            raise ValueError(f"Pedido não encontrado: {pedido_id}")
        
        # Determinar responsável pelo próximo passo
        responsavel = RESPONSABILIDADE_CANCELAMENTO.get(pedido.status, "CAC")
        
        # Atualizar pedido com dados de cancelamento
        pedido.data_solicitacao_cancelamento = datetime.now(timezone.utc)
        pedido.motivo_cancelamento = motivo
        
        # Se for solicitado pelo candidato, enviar para NRM
        if tipo == TipoCancelamento.SOLICITADO_CANDIDATO:
            prazo_nrm = datetime.now(timezone.utc) + timedelta(hours=PRAZO_NRM_HORAS)
            
            return {
                "status": "aguardando_nrm",
                "pedido_id": pedido_id,
                "tipo_cancelamento": tipo.value,
                "motivo": motivo,
                "responsavel_atual": responsavel,
                "prazo_nrm": prazo_nrm.isoformat(),
                "mensagem": f"Cancelamento encaminhado para NRM. Prazo de 48h para tentativa de reversão (até {prazo_nrm.strftime('%d/%m/%Y %H:%M')})",
                "proximos_passos": [
                    "NRM tentará reverter o cancelamento em até 48h",
                    "Se candidato confirmar cancelamento:",
                    f"  - {responsavel}: {'Solicitar dados bancários e abrir chamado financeiro' if responsavel == 'CAC' else 'Orientar abertura de requerimento via Portal do Aluno'}"
                ]
            }
        else:
            # Cancelamento automático ou pelo SENAI - processa direto
            pedido.status = "cancelado"
            await self.session.commit()
            
            return {
                "status": "cancelado",
                "pedido_id": pedido_id,
                "tipo_cancelamento": tipo.value,
                "motivo": motivo,
                "mensagem": "Pedido cancelado com sucesso"
            }
    
    async def registrar_resposta_nrm(
        self,
        pedido_id: str,
        revertido: bool,
        observacoes: str
    ) -> Dict[str, Any]:
        """
        Registra resposta do NRM sobre tentativa de reversão.
        """
        from src.infrastructure.persistence.models import PedidoModel
        
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.id == pedido_id)
        )
        pedido = result.scalar_one_or_none()
        
        if not pedido:
            raise ValueError(f"Pedido não encontrado: {pedido_id}")
        
        pedido.nrm_tentou_reversao = True
        pedido.data_reversao_nrm = datetime.now(timezone.utc)
        
        if revertido:
            # NRM conseguiu reverter - matrícula continua
            return {
                "status": "revertido",
                "pedido_id": pedido_id,
                "mensagem": "Cancelamento revertido pelo NRM. Matrícula continua normalmente.",
                "observacoes": observacoes
            }
        else:
            # NRM não conseguiu reverter - prosseguir com cancelamento
            responsavel = RESPONSABILIDADE_CANCELAMENTO.get(pedido.status, "CAC")
            
            return {
                "status": "cancelamento_confirmado",
                "pedido_id": pedido_id,
                "responsavel": responsavel,
                "mensagem": f"NRM não conseguiu reverter. Próximo passo: {responsavel}",
                "proximos_passos": self._get_proximos_passos_cancelamento(pedido.status, responsavel),
                "observacoes": observacoes
            }
    
    def _get_proximos_passos_cancelamento(self, status: str, responsavel: str) -> List[str]:
        """Retorna próximos passos baseado no status e responsável"""
        if responsavel == "CAC":
            return [
                "1. Solicitar dados bancários ao candidato",
                "2. Abrir chamado para o financeiro",
                "3. Aguardar processamento do reembolso (15 dias úteis)"
            ]
        else:  # CAA
            return [
                "1. Enviar e-mail padrão ao candidato",
                "2. Orientar abertura de requerimento via Portal do Aluno",
                "3. Acompanhar finalização do processo"
            ]
    
    async def verificar_prazo_nrm(self, pedido_id: str) -> Dict[str, Any]:
        """
        Verifica se prazo de 48h do NRM já expirou.
        """
        from src.infrastructure.persistence.models import PedidoModel
        
        result = await self.session.execute(
            select(PedidoModel).where(PedidoModel.id == pedido_id)
        )
        pedido = result.scalar_one_or_none()
        
        if not pedido or not pedido.data_solicitacao_cancelamento:
            return {"status": "nao_aplicavel", "mensagem": "Pedido não está em processo de cancelamento"}
        
        data_solicitacao = pedido.data_solicitacao_cancelamento
        if data_solicitacao.tzinfo is None:
            data_solicitacao = data_solicitacao.replace(tzinfo=timezone.utc)
        
        prazo_nrm = data_solicitacao + timedelta(hours=PRAZO_NRM_HORAS)
        agora = datetime.now(timezone.utc)
        
        horas_restantes = (prazo_nrm - agora).total_seconds() / 3600
        
        return {
            "pedido_id": pedido_id,
            "data_solicitacao": data_solicitacao.isoformat(),
            "prazo_nrm": prazo_nrm.isoformat(),
            "horas_restantes": round(horas_restantes, 1),
            "expirado": horas_restantes < 0,
            "nrm_respondeu": pedido.nrm_tentou_reversao or False
        }


# ==================== FUNÇÕES AUXILIARES ====================

def get_documentos_escolaridade() -> List[Dict[str, Any]]:
    """Retorna lista de documentos de escolaridade TOTVS"""
    return [
        {**doc, "codigo": cod}
        for cod, doc in DOCUMENTOS_ESCOLARIDADE_TOTVS.items()
    ]


def get_fluxo_validacao_escolaridade() -> Dict[str, Any]:
    """Retorna fluxos de validação de documentos de escolaridade"""
    return FLUXO_VALIDACAO_ESCOLARIDADE


def get_responsabilidades_cancelamento() -> Dict[str, str]:
    """Retorna mapa de responsabilidades por status"""
    return RESPONSABILIDADE_CANCELAMENTO


def get_tipos_cancelamento() -> List[Dict[str, str]]:
    """Retorna tipos de cancelamento disponíveis"""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in TipoCancelamento
    ]
