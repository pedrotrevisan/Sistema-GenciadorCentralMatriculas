"""
Router de Alertas Unificados para Assistentes
Consolida todos os alertas do sistema em um único endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from src.infrastructure.persistence.database import async_session
from src.infrastructure.persistence.models import PedidoModel, ReembolsoModel

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("/dashboard")
async def get_alertas_dashboard():
    """
    Retorna todos os alertas ativos para o dashboard de assistentes.
    
    Tipos de alerta:
    - critico: Pedidos parados há mais de 48h
    - sla_risco: Pedidos próximos do limite de SLA
    - reembolso: Reembolsos pendentes há muito tempo
    - vagas: Turmas com vagas esgotando
    """
    async with async_session() as session:
        alertas = []
        
        # 1. PEDIDOS CRÍTICOS (parados há mais de 48h em status pendente/em_analise)
        limite_48h = datetime.now(timezone.utc) - timedelta(hours=48)
        
        criticos_query = select(PedidoModel).where(
            and_(
                PedidoModel.updated_at < limite_48h,
                PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
            )
        ).order_by(PedidoModel.updated_at.asc()).limit(20)
        
        criticos_result = await session.execute(criticos_query)
        pedidos_criticos = criticos_result.scalars().all()
        
        for pedido in pedidos_criticos:
            horas_parado = int((datetime.now(timezone.utc) - pedido.updated_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
            alertas.append({
                "id": f"critico_{pedido.id}",
                "tipo": "critico",
                "prioridade": "alta",
                "icone": "alert-triangle",
                "cor": "red",
                "titulo": f"Pedido parado há {horas_parado}h",
                "descricao": f"{pedido.numero_protocolo} - {pedido.curso_nome}",
                "detalhes": {
                    "pedido_id": pedido.id,
                    "protocolo": pedido.numero_protocolo,
                    "status": pedido.status,
                    "horas_parado": horas_parado,
                    "curso": pedido.curso_nome
                },
                "acao": {
                    "label": "Ver Pedido",
                    "url": f"/admin/pedido/{pedido.id}"
                },
                "created_at": pedido.updated_at.isoformat() if pedido.updated_at else None
            })
        
        # 2. PEDIDOS EM RISCO DE SLA (24-48h parados)
        limite_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        
        risco_query = select(PedidoModel).where(
            and_(
                PedidoModel.updated_at < limite_24h,
                PedidoModel.updated_at >= limite_48h,
                PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
            )
        ).order_by(PedidoModel.updated_at.asc()).limit(10)
        
        risco_result = await session.execute(risco_query)
        pedidos_risco = risco_result.scalars().all()
        
        for pedido in pedidos_risco:
            horas_parado = int((datetime.now(timezone.utc) - pedido.updated_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
            alertas.append({
                "id": f"sla_risco_{pedido.id}",
                "tipo": "sla_risco",
                "prioridade": "media",
                "icone": "clock",
                "cor": "amber",
                "titulo": f"SLA em risco ({horas_parado}h)",
                "descricao": f"{pedido.numero_protocolo} - {pedido.curso_nome}",
                "detalhes": {
                    "pedido_id": pedido.id,
                    "protocolo": pedido.numero_protocolo,
                    "status": pedido.status,
                    "horas_parado": horas_parado
                },
                "acao": {
                    "label": "Ver Pedido",
                    "url": f"/admin/pedido/{pedido.id}"
                },
                "created_at": pedido.updated_at.isoformat() if pedido.updated_at else None
            })
        
        # 3. REEMBOLSOS PENDENTES (há mais de 5 dias)
        limite_5d = datetime.now(timezone.utc) - timedelta(days=5)
        
        reembolsos_query = select(ReembolsoModel).where(
            and_(
                ReembolsoModel.created_at < limite_5d,
                ReembolsoModel.status.in_(['aberto', 'aguardando_dados', 'no_financeiro'])
            )
        ).order_by(ReembolsoModel.created_at.asc()).limit(10)
        
        reembolsos_result = await session.execute(reembolsos_query)
        reembolsos_pendentes = reembolsos_result.scalars().all()
        
        for reembolso in reembolsos_pendentes:
            dias_pendente = int((datetime.now(timezone.utc) - reembolso.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400)
            alertas.append({
                "id": f"reembolso_{reembolso.id}",
                "tipo": "reembolso",
                "prioridade": "media" if dias_pendente < 10 else "alta",
                "icone": "dollar-sign",
                "cor": "orange",
                "titulo": f"Reembolso pendente há {dias_pendente} dias",
                "descricao": f"{reembolso.aluno_nome} - {reembolso.curso}",
                "detalhes": {
                    "reembolso_id": reembolso.id,
                    "aluno": reembolso.aluno_nome,
                    "curso": reembolso.curso,
                    "status": reembolso.status,
                    "dias_pendente": dias_pendente
                },
                "acao": {
                    "label": "Ver Reembolso",
                    "url": f"/reembolsos?id={reembolso.id}"
                },
                "created_at": reembolso.created_at.isoformat() if reembolso.created_at else None
            })
        
        # 4. TURMAS LOTANDO (>= 90% de ocupação)
        try:
            from src.infrastructure.persistence.models_turmas import TurmaModel
            
            turmas_query = select(TurmaModel).where(TurmaModel.ativo == True)
            turmas_result = await session.execute(turmas_query)
            turmas = turmas_result.scalars().all()
            
            for turma in turmas:
                if turma.vagas_totais > 0:
                    ocupacao = (turma.vagas_ocupadas / turma.vagas_totais) * 100
                    if ocupacao >= 90:
                        vagas_disponiveis = turma.vagas_totais - turma.vagas_ocupadas
                        alertas.append({
                            "id": f"vagas_{turma.id}",
                            "tipo": "vagas",
                            "prioridade": "alta" if ocupacao >= 95 else "media",
                            "icone": "graduation-cap",
                            "cor": "purple",
                            "titulo": f"Turma quase lotada ({ocupacao:.0f}%)",
                            "descricao": f"{turma.nome_curso} - {vagas_disponiveis} vaga(s) restante(s)",
                            "detalhes": {
                                "turma_id": turma.id,
                                "curso": turma.nome_curso,
                                "turno": turma.turno,
                                "ocupacao": ocupacao,
                                "vagas_disponiveis": vagas_disponiveis
                            },
                            "acao": {
                                "label": "Ver Painel",
                                "url": "/painel-vagas"
                            },
                            "created_at": None
                        })
        except Exception as e:
            pass  # Se não houver tabela de turmas, ignora
        
        # Ordenar por prioridade (alta > media > baixa)
        prioridade_ordem = {"alta": 0, "media": 1, "baixa": 2}
        alertas.sort(key=lambda x: prioridade_ordem.get(x["prioridade"], 2))
        
        # Estatísticas
        stats = {
            "total": len(alertas),
            "criticos": len([a for a in alertas if a["tipo"] == "critico"]),
            "sla_risco": len([a for a in alertas if a["tipo"] == "sla_risco"]),
            "reembolsos": len([a for a in alertas if a["tipo"] == "reembolso"]),
            "vagas": len([a for a in alertas if a["tipo"] == "vagas"])
        }
        
        return {
            "alertas": alertas,
            "estatisticas": stats,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


@router.get("/contagem")
async def get_contagem_alertas():
    """Retorna apenas a contagem de alertas (para badge no header)"""
    async with async_session() as session:
        # Pedidos críticos (>48h)
        limite_48h = datetime.now(timezone.utc) - timedelta(hours=48)
        criticos_count = await session.execute(
            select(func.count(PedidoModel.id)).where(
                and_(
                    PedidoModel.updated_at < limite_48h,
                    PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
                )
            )
        )
        total_criticos = criticos_count.scalar() or 0
        
        # Pedidos em risco (24-48h)
        limite_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        risco_count = await session.execute(
            select(func.count(PedidoModel.id)).where(
                and_(
                    PedidoModel.updated_at < limite_24h,
                    PedidoModel.updated_at >= limite_48h,
                    PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
                )
            )
        )
        total_risco = risco_count.scalar() or 0
        
        # Reembolsos pendentes (>5 dias)
        limite_5d = datetime.now(timezone.utc) - timedelta(days=5)
        reembolsos_count = await session.execute(
            select(func.count(ReembolsoModel.id)).where(
                and_(
                    ReembolsoModel.created_at < limite_5d,
                    ReembolsoModel.status.in_(['aberto', 'aguardando_dados', 'no_financeiro'])
                )
            )
        )
        total_reembolsos = reembolsos_count.scalar() or 0
        
        return {
            "total": total_criticos + total_risco + total_reembolsos,
            "criticos": total_criticos,
            "sla_risco": total_risco,
            "reembolsos": total_reembolsos
        }
