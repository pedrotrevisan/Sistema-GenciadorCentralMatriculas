"""
Router para Painel de Vagas - Visão simplificada de ocupação
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from src.infrastructure.persistence.database import get_session
from src.domain.entities import Usuario
from .dependencies import get_current_user

router = APIRouter(prefix="/painel-vagas", tags=["Painel de Vagas"])

# Alias para manter consistência
get_db_session = get_session


# ============== INIT TABLE ==============

async def init_painel_turmas(session: AsyncSession):
    """Cria tabela simplificada de turmas para o painel"""
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS painel_turmas (
            id TEXT PRIMARY KEY,
            codigo_turma TEXT UNIQUE NOT NULL,
            nome_curso TEXT NOT NULL,
            turno TEXT NOT NULL,
            vagas_totais INTEGER NOT NULL DEFAULT 40,
            vagas_ocupadas INTEGER DEFAULT 0,
            periodo_letivo TEXT,
            modalidade TEXT DEFAULT 'CHP',
            status TEXT DEFAULT 'aberto',
            created_at TEXT,
            updated_at TEXT
        )
    """))
    await session.commit()


# ============== ENDPOINTS ==============

@router.get("/periodos")
async def listar_periodos(
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Lista períodos letivos disponíveis"""
    await init_painel_turmas(session)
    result = await session.execute(
        text("SELECT DISTINCT periodo_letivo FROM painel_turmas WHERE periodo_letivo IS NOT NULL ORDER BY periodo_letivo DESC")
    )
    periodos = [row[0] for row in result.fetchall()]
    return {"periodos": periodos}


@router.get("/dashboard")
async def dashboard_vagas(
    periodo: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Dashboard visual de ocupação de vagas"""
    await init_painel_turmas(session)
    
    where = "WHERE 1=1"
    params = {}
    if periodo:
        where += " AND periodo_letivo = :periodo"
        params["periodo"] = periodo
    
    # Totais
    result = await session.execute(
        text(f"""
            SELECT 
                COUNT(*) as total_turmas,
                COALESCE(SUM(vagas_totais), 0) as total_vagas,
                COALESCE(SUM(vagas_ocupadas), 0) as total_ocupadas
            FROM painel_turmas {where}
        """),
        params
    )
    row = result.fetchone()
    total_turmas = row[0] or 0
    total_vagas = row[1] or 0
    total_ocupadas = row[2] or 0
    
    # Turmas lotando (>= 90%)
    result = await session.execute(
        text(f"""
            SELECT COUNT(*) FROM painel_turmas 
            {where} AND vagas_ocupadas >= (vagas_totais * 0.9) AND vagas_totais > 0
        """),
        params
    )
    turmas_lotando = result.scalar() or 0
    
    # Por curso
    result = await session.execute(
        text(f"""
            SELECT 
                nome_curso,
                SUM(vagas_totais) as vagas,
                SUM(vagas_ocupadas) as ocupadas
            FROM painel_turmas {where}
            GROUP BY nome_curso
            ORDER BY nome_curso
        """),
        params
    )
    por_curso = []
    for row in result.fetchall():
        vagas = row[1] or 0
        ocupadas = row[2] or 0
        por_curso.append({
            "curso": row[0],
            "vagas_totais": vagas,
            "vagas_ocupadas": ocupadas,
            "vagas_disponiveis": vagas - ocupadas,
            "percentual": round((ocupadas / vagas * 100) if vagas > 0 else 0, 1)
        })
    
    # Por turno
    result = await session.execute(
        text(f"""
            SELECT 
                turno,
                SUM(vagas_totais) as vagas,
                SUM(vagas_ocupadas) as ocupadas
            FROM painel_turmas {where}
            GROUP BY turno
        """),
        params
    )
    por_turno = []
    for row in result.fetchall():
        vagas = row[1] or 0
        ocupadas = row[2] or 0
        por_turno.append({
            "turno": row[0],
            "vagas_totais": vagas,
            "vagas_ocupadas": ocupadas,
            "percentual": round((ocupadas / vagas * 100) if vagas > 0 else 0, 1)
        })
    
    # Alertas - turmas críticas
    result = await session.execute(
        text(f"""
            SELECT codigo_turma, nome_curso, turno, vagas_totais, vagas_ocupadas
            FROM painel_turmas
            {where} AND vagas_ocupadas >= (vagas_totais * 0.85) AND vagas_totais > 0
            ORDER BY (vagas_ocupadas * 1.0 / vagas_totais) DESC
            LIMIT 10
        """),
        params
    )
    alertas = []
    for row in result.fetchall():
        vagas = row[3] or 0
        ocupadas = row[4] or 0
        alertas.append({
            "codigo": row[0],
            "curso": row[1],
            "turno": row[2],
            "vagas_totais": vagas,
            "vagas_ocupadas": ocupadas,
            "vagas_disponiveis": vagas - ocupadas,
            "percentual": round((ocupadas / vagas * 100) if vagas > 0 else 0, 1),
            "status": "lotado" if ocupadas >= vagas else "lotando"
        })
    
    return {
        "resumo": {
            "total_turmas": total_turmas,
            "total_vagas": total_vagas,
            "total_ocupadas": total_ocupadas,
            "vagas_disponiveis": total_vagas - total_ocupadas,
            "percentual_ocupacao": round((total_ocupadas / total_vagas * 100) if total_vagas > 0 else 0, 1),
            "turmas_lotando": turmas_lotando
        },
        "por_curso": por_curso,
        "por_turno": por_turno,
        "alertas": alertas
    }


@router.get("/turmas")
async def listar_turmas_painel(
    periodo: Optional[str] = None,
    turno: Optional[str] = None,
    busca: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Lista turmas com ocupação"""
    await init_painel_turmas(session)
    
    where = ["1=1"]
    params = {}
    
    if periodo:
        where.append("periodo_letivo = :periodo")
        params["periodo"] = periodo
    if turno:
        where.append("turno = :turno")
        params["turno"] = turno
    if busca:
        where.append("(nome_curso LIKE :busca OR codigo_turma LIKE :busca)")
        params["busca"] = f"%{busca}%"
    
    where_sql = " AND ".join(where)
    
    result = await session.execute(
        text(f"""
            SELECT * FROM painel_turmas
            WHERE {where_sql}
            ORDER BY nome_curso, turno
        """),
        params
    )
    
    turmas = []
    for row in result.fetchall():
        t = dict(row._mapping)
        vagas = t["vagas_totais"] or 0
        ocupadas = t["vagas_ocupadas"] or 0
        t["vagas_disponiveis"] = vagas - ocupadas
        t["percentual"] = round((ocupadas / vagas * 100) if vagas > 0 else 0, 1)
        t["status_ocupacao"] = "lotado" if ocupadas >= vagas else ("lotando" if ocupadas >= vagas * 0.85 else "disponivel")
        turmas.append(t)
    
    return {"turmas": turmas, "total": len(turmas)}


@router.post("/turmas")
async def criar_turma_painel(
    codigo_turma: str,
    nome_curso: str,
    turno: str,
    vagas_totais: int,
    vagas_ocupadas: int = 0,
    periodo_letivo: str = "2026.1",
    modalidade: str = "CHP",
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Cria ou atualiza turma no painel"""
    await init_painel_turmas(session)
    
    # Verificar se existe
    result = await session.execute(
        text("SELECT id FROM painel_turmas WHERE codigo_turma = :codigo"),
        {"codigo": codigo_turma}
    )
    existing = result.fetchone()
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        await session.execute(
            text("""
                UPDATE painel_turmas SET
                    nome_curso = :nome, turno = :turno, vagas_totais = :vagas,
                    vagas_ocupadas = :ocupadas, periodo_letivo = :periodo,
                    modalidade = :modalidade, updated_at = :updated
                WHERE codigo_turma = :codigo
            """),
            {
                "codigo": codigo_turma, "nome": nome_curso, "turno": turno,
                "vagas": vagas_totais, "ocupadas": vagas_ocupadas,
                "periodo": periodo_letivo, "modalidade": modalidade, "updated": now
            }
        )
        await session.commit()
        return {"message": "Turma atualizada", "id": existing[0]}
    else:
        turma_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO painel_turmas (
                    id, codigo_turma, nome_curso, turno, vagas_totais,
                    vagas_ocupadas, periodo_letivo, modalidade, status,
                    created_at, updated_at
                ) VALUES (
                    :id, :codigo, :nome, :turno, :vagas,
                    :ocupadas, :periodo, :modalidade, 'aberto',
                    :created, :updated
                )
            """),
            {
                "id": turma_id, "codigo": codigo_turma, "nome": nome_curso,
                "turno": turno, "vagas": vagas_totais, "ocupadas": vagas_ocupadas,
                "periodo": periodo_letivo, "modalidade": modalidade,
                "created": now, "updated": now
            }
        )
        await session.commit()
        return {"message": "Turma criada", "id": turma_id}


@router.put("/turmas/{turma_id}/ocupacao")
async def atualizar_ocupacao_turma(
    turma_id: str,
    vagas_ocupadas: int,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza ocupação de uma turma"""
    await init_painel_turmas(session)
    
    result = await session.execute(
        text("SELECT vagas_totais FROM painel_turmas WHERE id = :id"),
        {"id": turma_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    await session.execute(
        text("""
            UPDATE painel_turmas 
            SET vagas_ocupadas = :ocupadas, updated_at = :updated
            WHERE id = :id
        """),
        {
            "id": turma_id,
            "ocupadas": vagas_ocupadas,
            "updated": datetime.now(timezone.utc).isoformat()
        }
    )
    await session.commit()
    
    return {"message": "Ocupação atualizada"}


@router.delete("/turmas/{turma_id}")
async def deletar_turma_painel(
    turma_id: str,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Deleta turma do painel"""
    if current_user.perfil not in ["admin", "coordenador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    await init_painel_turmas(session)
    
    result = await session.execute(
        text("DELETE FROM painel_turmas WHERE id = :id"),
        {"id": turma_id}
    )
    await session.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    return {"message": "Turma deletada"}


@router.post("/importar-cimatec-2026")
async def importar_cursos_cimatec(
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Importa os cursos técnicos do CIMATEC 2026.1 da planilha CHP"""
    await init_painel_turmas(session)
    
    # Dados da planilha "Quantitativo de matrícula CHP 2026.1"
    cursos = [
        {"codigo": "B101622", "nome": "Técnico em Mecânica", "turno": "NOTURNO", "vagas": 40, "ocupadas": 26},
        {"codigo": "B101623", "nome": "Técnico em Eletrotécnica", "turno": "NOTURNO", "vagas": 42, "ocupadas": 16},
        {"codigo": "B101625", "nome": "Técnico em Desenvolvimento de Sistemas", "turno": "NOTURNO", "vagas": 40, "ocupadas": 12},
        {"codigo": "B101626", "nome": "Técnico em Multimídia", "turno": "NOTURNO", "vagas": 40, "ocupadas": 6},
        {"codigo": "B101627", "nome": "Técnico em Logística", "turno": "NOTURNO", "vagas": 42, "ocupadas": 1},
        {"codigo": "B101628", "nome": "Técnico em Mecatrônica", "turno": "NOTURNO", "vagas": 42, "ocupadas": 0},
        {"codigo": "B101629", "nome": "Técnico em Biotecnologia", "turno": "MATUTINO", "vagas": 30, "ocupadas": 1},
        {"codigo": "B101630", "nome": "Técnico em Petroquímica", "turno": "NOTURNO", "vagas": 40, "ocupadas": 1},
        {"codigo": "B101631", "nome": "Técnico em Redes de Computadores", "turno": "NOTURNO", "vagas": 40, "ocupadas": 1},
        {"codigo": "B101632", "nome": "Técnico em Manutenção Automotiva", "turno": "NOTURNO", "vagas": 42, "ocupadas": 1},
        {"codigo": "CQP102885", "nome": "Mecânico de Usinagem Convencional", "turno": "MATUTINO", "vagas": 40, "ocupadas": 28},
    ]
    
    importados = 0
    atualizados = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for c in cursos:
        result = await session.execute(
            text("SELECT id FROM painel_turmas WHERE codigo_turma = :codigo"),
            {"codigo": c["codigo"]}
        )
        existing = result.fetchone()
        
        if existing:
            await session.execute(
                text("""
                    UPDATE painel_turmas SET
                        nome_curso = :nome, turno = :turno, vagas_totais = :vagas,
                        vagas_ocupadas = :ocupadas, updated_at = :updated
                    WHERE codigo_turma = :codigo
                """),
                {
                    "codigo": c["codigo"], "nome": c["nome"], "turno": c["turno"],
                    "vagas": c["vagas"], "ocupadas": c["ocupadas"], "updated": now
                }
            )
            atualizados += 1
        else:
            await session.execute(
                text("""
                    INSERT INTO painel_turmas (
                        id, codigo_turma, nome_curso, turno, vagas_totais,
                        vagas_ocupadas, periodo_letivo, modalidade, status,
                        created_at, updated_at
                    ) VALUES (
                        :id, :codigo, :nome, :turno, :vagas,
                        :ocupadas, '2026.1', 'CHP', 'aberto', :created, :updated
                    )
                """),
                {
                    "id": str(uuid.uuid4()), "codigo": c["codigo"], "nome": c["nome"],
                    "turno": c["turno"], "vagas": c["vagas"], "ocupadas": c["ocupadas"],
                    "created": now, "updated": now
                }
            )
            importados += 1
    
    await session.commit()
    
    return {
        "message": "Cursos CIMATEC 2026.1 importados com sucesso!",
        "importados": importados,
        "atualizados": atualizados,
        "total": len(cursos)
    }


@router.post("/duplicar-periodo")
async def duplicar_turmas_periodo(
    periodo_origem: str = Query(..., description="Período de origem (ex: 2026.1)"),
    periodo_destino: str = Query(..., description="Novo período (ex: 2026.2)"),
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Duplica todas as turmas de um período para outro, zerando a ocupação"""
    await init_painel_turmas(session)

    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Apenas administradores podem duplicar períodos")

    # Check if destination already has turmas
    existing = await session.execute(
        text("SELECT COUNT(*) FROM painel_turmas WHERE periodo_letivo = :dest"),
        {"dest": periodo_destino}
    )
    if (existing.scalar() or 0) > 0:
        raise HTTPException(status_code=409, detail=f"O período {periodo_destino} já possui turmas cadastradas")

    # Get source turmas
    result = await session.execute(
        text("SELECT codigo_turma, nome_curso, turno, vagas_totais, modalidade FROM painel_turmas WHERE periodo_letivo = :origem"),
        {"origem": periodo_origem}
    )
    turmas_origem = result.fetchall()

    if not turmas_origem:
        raise HTTPException(status_code=404, detail=f"Nenhuma turma encontrada no período {periodo_origem}")

    now = datetime.now(timezone.utc).isoformat()
    criadas = 0

    for t in turmas_origem:
        novo_codigo = f"{t[0]}-{periodo_destino.replace('.', '')}"
        await session.execute(
            text("""
                INSERT INTO painel_turmas (
                    id, codigo_turma, nome_curso, turno, vagas_totais,
                    vagas_ocupadas, periodo_letivo, modalidade, status,
                    created_at, updated_at
                ) VALUES (
                    :id, :codigo, :nome, :turno, :vagas,
                    0, :periodo, :modalidade, 'aberto', :created, :updated
                )
            """),
            {
                "id": str(uuid.uuid4()), "codigo": novo_codigo,
                "nome": t[1], "turno": t[2], "vagas": t[3],
                "periodo": periodo_destino, "modalidade": t[4] or "CHP",
                "created": now, "updated": now
            }
        )
        criadas += 1

    await session.commit()

    return {
        "message": f"{criadas} turmas duplicadas para o período {periodo_destino}",
        "periodo_origem": periodo_origem,
        "periodo_destino": periodo_destino,
        "turmas_criadas": criadas
    }
