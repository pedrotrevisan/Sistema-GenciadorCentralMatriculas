"""Serviço de Log de Atividades do Usuário"""
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.infrastructure.persistence.models import AtividadeUsuarioModel

logger = logging.getLogger(__name__)


# Mapeamento de tipos para descrições legíveis
TIPOS_ATIVIDADE = {
    "login": {"descricao": "Fez login no sistema", "icone": "log-in", "cor": "green"},
    "logout": {"descricao": "Fez logout do sistema", "icone": "log-out", "cor": "gray"},
    "criar_pedido": {"descricao": "Criou nova solicitação de matrícula", "icone": "file-plus", "cor": "blue"},
    "atualizar_pedido": {"descricao": "Atualizou solicitação de matrícula", "icone": "edit", "cor": "yellow"},
    "criar_pendencia": {"descricao": "Criou pendência documental", "icone": "file-warning", "cor": "orange"},
    "atualizar_pendencia": {"descricao": "Atualizou pendência documental", "icone": "file-check", "cor": "yellow"},
    "criar_reembolso": {"descricao": "Criou solicitação de reembolso", "icone": "dollar-sign", "cor": "purple"},
    "atualizar_reembolso": {"descricao": "Atualizou reembolso", "icone": "credit-card", "cor": "yellow"},
    "atribuir_demanda": {"descricao": "Atribuiu demanda a responsável", "icone": "user-check", "cor": "cyan"},
    "alterar_perfil": {"descricao": "Alterou dados do perfil", "icone": "user-cog", "cor": "blue"},
    "alterar_senha": {"descricao": "Alterou a senha", "icone": "key", "cor": "red"},
    "exportar_totvs": {"descricao": "Exportou para TOTVS", "icone": "download", "cor": "green"},
    "importar_lote": {"descricao": "Importou dados em lote", "icone": "upload", "cor": "blue"},
    "criar_contato": {"descricao": "Registrou contato com aluno", "icone": "phone", "cor": "teal"},
    "criar_tarefa": {"descricao": "Criou tarefa no checklist", "icone": "check-square", "cor": "purple"},
    "criar_artigo": {"descricao": "Criou artigo na base de conhecimento", "icone": "book", "cor": "indigo"},
    "visualizar_pedido": {"descricao": "Visualizou detalhes de solicitação", "icone": "eye", "cor": "gray"},
}


async def registrar_atividade(
    session: AsyncSession,
    usuario_id: str,
    usuario_nome: str,
    tipo: str,
    descricao: Optional[str] = None,
    entidade_tipo: Optional[str] = None,
    entidade_id: Optional[str] = None,
    entidade_nome: Optional[str] = None,
    detalhes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AtividadeUsuarioModel:
    """
    Registra uma atividade do usuário no sistema.
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário que realizou a ação
        usuario_nome: Nome do usuário
        tipo: Tipo da atividade (login, criar_pedido, etc)
        descricao: Descrição personalizada (opcional, usa padrão se não fornecido)
        entidade_tipo: Tipo da entidade relacionada (pedido, pendencia, etc)
        entidade_id: ID da entidade relacionada
        entidade_nome: Nome/identificador da entidade (protocolo, nome, etc)
        detalhes: Dicionário com detalhes adicionais
        ip_address: IP do usuário
        user_agent: User agent do navegador
    
    Returns:
        AtividadeUsuarioModel criado
    """
    try:
        # Usar descrição padrão se não fornecida
        if not descricao:
            info_tipo = TIPOS_ATIVIDADE.get(tipo, {"descricao": tipo})
            descricao = info_tipo["descricao"]
        
        atividade = AtividadeUsuarioModel(
            id=str(uuid.uuid4()),
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            tipo=tipo,
            descricao=descricao,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            entidade_nome=entidade_nome,
            detalhes=detalhes,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc)
        )
        
        session.add(atividade)
        await session.commit()
        
        logger.info(f"Atividade registrada: {tipo} por {usuario_nome}")
        return atividade
        
    except Exception as e:
        logger.error(f"Erro ao registrar atividade: {e}")
        await session.rollback()
        raise


async def listar_atividades_usuario(
    session: AsyncSession,
    usuario_id: str,
    limite: int = 50,
    tipos: Optional[list] = None
) -> list:
    """
    Lista as atividades recentes de um usuário.
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário
        limite: Número máximo de atividades
        tipos: Filtrar por tipos específicos
    
    Returns:
        Lista de atividades formatadas
    """
    query = select(AtividadeUsuarioModel).where(
        AtividadeUsuarioModel.usuario_id == usuario_id
    )
    
    if tipos:
        query = query.where(AtividadeUsuarioModel.tipo.in_(tipos))
    
    query = query.order_by(desc(AtividadeUsuarioModel.created_at)).limit(limite)
    
    result = await session.execute(query)
    atividades = result.scalars().all()
    
    # Formatar para retorno
    atividades_formatadas = []
    for a in atividades:
        info_tipo = TIPOS_ATIVIDADE.get(a.tipo, {"icone": "activity", "cor": "gray"})
        
        atividades_formatadas.append({
            "id": a.id,
            "tipo": a.tipo,
            "tipo_icone": info_tipo.get("icone", "activity"),
            "tipo_cor": info_tipo.get("cor", "gray"),
            "descricao": a.descricao,
            "entidade_tipo": a.entidade_tipo,
            "entidade_id": a.entidade_id,
            "entidade_nome": a.entidade_nome,
            "detalhes": a.detalhes,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })
    
    return atividades_formatadas


def get_tipos_atividade() -> list:
    """Retorna lista de tipos de atividade com seus metadados"""
    return [
        {"tipo": k, **v}
        for k, v in TIPOS_ATIVIDADE.items()
    ]
