"""Router para Dashboard de Produtividade da Equipe"""
from fastapi import APIRouter, Query
from sqlalchemy import select, func, case, and_, text
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from src.infrastructure.persistence.database import async_session
from src.infrastructure.persistence.models import (
    PedidoModel, AuditoriaModel, UsuarioModel, ReembolsoModel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/produtividade", tags=["Produtividade"])


@router.get("/dashboard")
async def get_dashboard_produtividade(
    periodo: Optional[str] = Query("30d", description="Período: 7d, 15d, 30d, 90d, all")
):
    """
    Dashboard completo de produtividade da equipe.
    Mostra métricas de trabalho por assistente/admin.
    """
    async with async_session() as session:
        # Calculate date filter
        now = datetime.now(timezone.utc)
        if periodo == "7d":
            data_inicio = now - timedelta(days=7)
            label_periodo = "Últimos 7 dias"
        elif periodo == "15d":
            data_inicio = now - timedelta(days=15)
            label_periodo = "Últimos 15 dias"
        elif periodo == "90d":
            data_inicio = now - timedelta(days=90)
            label_periodo = "Últimos 90 dias"
        elif periodo == "all":
            data_inicio = datetime(2020, 1, 1, tzinfo=timezone.utc)
            label_periodo = "Todo o período"
        else:
            data_inicio = now - timedelta(days=30)
            label_periodo = "Últimos 30 dias"

        # 1. Get all active assistants and admins
        usuarios_result = await session.execute(
            select(UsuarioModel)
            .where(UsuarioModel.ativo == True)
            .where(UsuarioModel.role.in_(["admin", "assistente"]))
        )
        usuarios = usuarios_result.scalars().all()
        usuarios_map = {u.id: {"nome": u.nome, "email": u.email, "role": u.role} for u in usuarios}

        # 2. Pedidos created by each consultor in period
        pedidos_criados = await session.execute(
            select(
                PedidoModel.consultor_id,
                PedidoModel.consultor_nome,
                func.count(PedidoModel.id).label("total")
            )
            .where(PedidoModel.created_at >= data_inicio)
            .group_by(PedidoModel.consultor_id, PedidoModel.consultor_nome)
        )
        pedidos_por_consultor = {row[0]: {"nome": row[1], "total": row[2]} for row in pedidos_criados.fetchall()}

        # 3. Auditoria actions per user (status changes, exports, etc.)
        auditorias_result = await session.execute(
            select(
                AuditoriaModel.usuario_id,
                AuditoriaModel.acao,
                func.count(AuditoriaModel.id).label("total")
            )
            .where(AuditoriaModel.timestamp >= data_inicio)
            .group_by(AuditoriaModel.usuario_id, AuditoriaModel.acao)
        )
        auditorias_por_usuario = {}
        for row in auditorias_result.fetchall():
            uid = row[0]
            if uid not in auditorias_por_usuario:
                auditorias_por_usuario[uid] = {}
            auditorias_por_usuario[uid][row[1]] = row[2]

        # 4. Pedidos where user is responsavel
        responsaveis_result = await session.execute(
            select(
                PedidoModel.responsavel_id,
                PedidoModel.responsavel_nome,
                PedidoModel.status,
                func.count(PedidoModel.id).label("total")
            )
            .where(PedidoModel.responsavel_id.isnot(None))
            .where(PedidoModel.updated_at >= data_inicio)
            .group_by(PedidoModel.responsavel_id, PedidoModel.responsavel_nome, PedidoModel.status)
        )
        responsavel_data = {}
        for row in responsaveis_result.fetchall():
            uid = row[0]
            if uid not in responsavel_data:
                responsavel_data[uid] = {"nome": row[1], "total": 0, "concluidos": 0}
            responsavel_data[uid]["total"] += row[3]
            if row[2] in ("aprovado", "realizado", "exportado", "matriculado"):
                responsavel_data[uid]["concluidos"] += row[3]

        # 5. Reembolsos handled per user
        reembolsos_result = await session.execute(
            select(
                ReembolsoModel.responsavel_id,
                ReembolsoModel.responsavel_nome,
                ReembolsoModel.status,
                func.count(ReembolsoModel.id).label("total")
            )
            .where(ReembolsoModel.responsavel_id.isnot(None))
            .where(ReembolsoModel.updated_at >= data_inicio)
            .group_by(ReembolsoModel.responsavel_id, ReembolsoModel.responsavel_nome, ReembolsoModel.status)
        )
        reembolsos_data = {}
        for row in reembolsos_result.fetchall():
            uid = row[0]
            if uid not in reembolsos_data:
                reembolsos_data[uid] = {"nome": row[1], "total": 0, "concluidos": 0}
            reembolsos_data[uid]["total"] += row[3]
            if row[2] in ("pago", "concluido"):
                reembolsos_data[uid]["concluidos"] += row[3]

        # 6. Build per-member productivity data
        membros = []
        all_user_ids = set(usuarios_map.keys()) | set(pedidos_por_consultor.keys())

        for uid in all_user_ids:
            info = usuarios_map.get(uid, {})
            nome = info.get("nome") or pedidos_por_consultor.get(uid, {}).get("nome", "Desconhecido")
            role = info.get("role", "")

            pedidos_count = pedidos_por_consultor.get(uid, {}).get("total", 0)
            audits = auditorias_por_usuario.get(uid, {})
            status_changes = audits.get("ATUALIZACAO_STATUS", 0)
            criacoes = audits.get("CRIACAO", 0)
            total_auditorias = sum(audits.values())

            resp = responsavel_data.get(uid, {"total": 0, "concluidos": 0})
            reemb = reembolsos_data.get(uid, {"total": 0, "concluidos": 0})

            total_acoes = pedidos_count + total_auditorias + resp["total"] + reemb["total"]

            membros.append({
                "usuario_id": uid,
                "nome": nome,
                "role": role,
                "pedidos_criados": pedidos_count,
                "alteracoes_status": status_changes,
                "total_auditorias": total_auditorias,
                "pedidos_atribuidos": resp["total"],
                "pedidos_concluidos": resp["concluidos"],
                "reembolsos_tratados": reemb["total"],
                "reembolsos_concluidos": reemb["concluidos"],
                "total_acoes": total_acoes
            })

        # Sort by total actions descending
        membros.sort(key=lambda x: x["total_acoes"], reverse=True)

        # 7. Global KPIs
        total_pedidos_periodo = await session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.created_at >= data_inicio)
        )
        total_pedidos = total_pedidos_periodo.scalar() or 0

        total_aprovados_periodo = await session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.created_at >= data_inicio)
            .where(PedidoModel.status.in_(["aprovado", "realizado", "exportado", "matriculado"]))
        )
        total_aprovados = total_aprovados_periodo.scalar() or 0

        total_reembolsos_periodo = await session.execute(
            select(func.count(ReembolsoModel.id))
            .where(ReembolsoModel.created_at >= data_inicio)
        )
        total_reembolsos = total_reembolsos_periodo.scalar() or 0

        total_auditorias_periodo = await session.execute(
            select(func.count(AuditoriaModel.id))
            .where(AuditoriaModel.timestamp >= data_inicio)
        )
        total_auds = total_auditorias_periodo.scalar() or 0

        dias_periodo = max((now - data_inicio).days, 1)
        media_diaria = round(total_pedidos / dias_periodo, 1)

        # 8. Daily evolution (last 14 days max)
        dias_evolucao = min(dias_periodo, 14)
        evolucao = []
        for i in range(dias_evolucao - 1, -1, -1):
            dia = now - timedelta(days=i)
            dia_inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
            dia_fim = dia.replace(hour=23, minute=59, second=59, microsecond=999999)

            pedidos_dia = await session.execute(
                select(func.count(PedidoModel.id))
                .where(PedidoModel.created_at >= dia_inicio)
                .where(PedidoModel.created_at <= dia_fim)
            )
            auds_dia = await session.execute(
                select(func.count(AuditoriaModel.id))
                .where(AuditoriaModel.timestamp >= dia_inicio)
                .where(AuditoriaModel.timestamp <= dia_fim)
            )

            evolucao.append({
                "data": dia.strftime("%d/%m"),
                "pedidos": pedidos_dia.scalar() or 0,
                "acoes": auds_dia.scalar() or 0
            })

        return {
            "periodo": label_periodo,
            "kpis": {
                "total_pedidos": total_pedidos,
                "total_aprovados": total_aprovados,
                "total_reembolsos": total_reembolsos,
                "total_auditorias": total_auds,
                "media_diaria_pedidos": media_diaria,
                "membros_ativos": len([m for m in membros if m["total_acoes"] > 0])
            },
            "membros": membros,
            "evolucao_diaria": evolucao,
            "generated_at": now.isoformat()
        }
