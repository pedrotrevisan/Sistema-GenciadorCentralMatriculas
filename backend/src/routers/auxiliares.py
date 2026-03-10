"""
Router de Dados Auxiliares
Contém rotas para status-pedido e outros dados auxiliares
"""
from fastapi import APIRouter
from src.domain.value_objects import StatusPedido

router = APIRouter(tags=["Auxiliares"])


@router.get("/status-pedido")
async def listar_status():
    """Lista status disponíveis com metadados completos"""
    return StatusPedido.get_all_with_metadata()


@router.get("/status-pedido/fluxo")
async def get_fluxo_status():
    """Retorna o fluxo principal de status na ordem correta"""
    return {
        "fluxo_principal": [
            {
                "value": s.value,
                "label": s.label,
                "cor": s.cor,
                "icone": s.icone
            }
            for s in StatusPedido.get_fluxo_principal()
        ],
        "status_alternativos": [
            {"value": "nao_atende_requisito", "label": "Não Atende Requisito", "cor": "red"},
            {"value": "cancelado", "label": "Cancelado", "cor": "red"},
            {"value": "trancado", "label": "Trancado", "cor": "orange"},
            {"value": "transferido", "label": "Transferido", "cor": "cyan"}
        ]
    }
