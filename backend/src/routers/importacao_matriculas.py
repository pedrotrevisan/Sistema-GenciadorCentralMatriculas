"""
Router para Importação em Lote de Matrículas
Permite importar múltiplos alunos de planilhas Excel/CSV
"""
from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import pandas as pd
import io
import uuid
import re

from .dependencies import get_current_user
from ..infrastructure.persistence.mongodb import db
from ..domain.entities import Usuario

router = APIRouter(prefix="/importacao", tags=["Importação de Matrículas"])


class AlunoPreview(BaseModel):
    linha: int
    nome: str
    cpf: str
    email: str
    telefone: str
    valido: bool
    erros: List[str]


class ValidacaoResult(BaseModel):
    sucesso: bool
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    preview: List[AlunoPreview]


class ErroImportacao(BaseModel):
    linha: int
    erro: str


class ImportacaoResult(BaseModel):
    pedidos_criados: int
    alunos_importados: int
    erros: List[ErroImportacao]


def validar_cpf(cpf: str) -> bool:
    """Valida CPF básico (11 dígitos)"""
    cpf_limpo = re.sub(r'[^\d]', '', str(cpf))
    return len(cpf_limpo) == 11


def validar_email(email: str) -> bool:
    """Valida formato de email"""
    if not email or pd.isna(email):
        return False
    return '@' in str(email) and '.' in str(email)


def limpar_telefone(telefone) -> str:
    """Limpa e formata telefone"""
    if pd.isna(telefone):
        return ""
    return re.sub(r'[^\d]', '', str(telefone))[:11]


def limpar_cpf(cpf) -> str:
    """Limpa CPF mantendo apenas dígitos"""
    if pd.isna(cpf):
        return ""
    return re.sub(r'[^\d]', '', str(cpf))[:11]


def formatar_nome(nome: str) -> str:
    """Formata nome próprio com capitalização correta"""
    if not nome or pd.isna(nome):
        return ""
    
    # Palavras que devem ficar em minúsculo
    preposicoes = {'de', 'da', 'do', 'das', 'dos', 'e'}
    
    palavras = str(nome).strip().split()
    resultado = []
    
    for i, palavra in enumerate(palavras):
        palavra_lower = palavra.lower()
        if i > 0 and palavra_lower in preposicoes:
            resultado.append(palavra_lower)
        else:
            resultado.append(palavra.capitalize())
    
    return ' '.join(resultado)


@router.get("/template")
async def download_template():
    """
    Baixa template Excel para importação de alunos
    """
    # Criar DataFrame com colunas do template
    df = pd.DataFrame(columns=[
        'NOME',
        'CPF',
        'EMAIL',
        'TELEFONE',
        'DATA_NASCIMENTO',
        'RG',
        'RG_ORGAO',
        'RG_UF',
        'ENDERECO_CEP',
        'ENDERECO_LOGRADOURO',
        'ENDERECO_NUMERO',
        'ENDERECO_COMPLEMENTO',
        'ENDERECO_BAIRRO',
        'ENDERECO_CIDADE',
        'ENDERECO_UF',
        'OBSERVACOES'
    ])
    
    # Adicionar linha de exemplo
    df.loc[0] = [
        'João da Silva Santos',
        '123.456.789-00',
        'joao.silva@email.com',
        '(71) 99999-9999',
        '15/05/1990',
        '1234567',
        'SSP',
        'BA',
        '40000-000',
        'Rua das Flores',
        '123',
        'Apto 101',
        'Centro',
        'Salvador',
        'BA',
        'Aluno transferido'
    ]
    
    # Criar buffer Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alunos')
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=template_importacao_matriculas.xlsx"
        }
    )


@router.post("/validar", response_model=ValidacaoResult)
async def validar_arquivo(
    file: UploadFile = File(...),
    curso_id: str = Query(..., description="ID do curso"),
    projeto_id: Optional[str] = Query(None, description="ID do projeto"),
    empresa_id: Optional[str] = Query(None, description="ID da empresa"),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Valida arquivo Excel/CSV antes da importação
    """
    # Verificar extensão
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Formato inválido. Use .xlsx, .xls ou .csv")
    
    # Ler arquivo
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar nomes das colunas
    df.columns = [col.upper().strip() for col in df.columns]
    
    # Mapear colunas alternativas
    column_mapping = {
        'ALUNO': 'NOME',
        'NOME COMPLETO': 'NOME',
        'NOME_COMPLETO': 'NOME',
        'E-MAIL': 'EMAIL',
        'E_MAIL': 'EMAIL',
        'TELEFONE1': 'TELEFONE',
        'TELEFONE 1': 'TELEFONE',
        'CEP': 'ENDERECO_CEP',
        'LOGRADOURO': 'ENDERECO_LOGRADOURO',
        'NUMERO': 'ENDERECO_NUMERO',
        'COMPLEMENTO': 'ENDERECO_COMPLEMENTO',
        'BAIRRO': 'ENDERECO_BAIRRO',
        'CIDADE': 'ENDERECO_CIDADE',
        'UF': 'ENDERECO_UF',
        'ESTADO': 'ENDERECO_UF'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Verificar coluna obrigatória
    if 'NOME' not in df.columns:
        raise HTTPException(
            status_code=400, 
            detail="Planilha deve ter coluna NOME ou ALUNO"
        )
    
    # Validar cada linha
    preview = []
    linhas_validas = 0
    linhas_com_erro = 0
    
    for idx, row in df.iterrows():
        linha_num = idx + 2  # +2 porque Excel começa em 1 e tem header
        erros = []
        
        nome = str(row.get('NOME', '')).strip() if pd.notna(row.get('NOME')) else ''
        cpf_raw = row.get('CPF', '')
        cpf = limpar_cpf(cpf_raw)
        email = str(row.get('EMAIL', '')).strip() if pd.notna(row.get('EMAIL')) else ''
        telefone = limpar_telefone(row.get('TELEFONE', ''))
        
        # Validações
        if not nome or len(nome) < 3:
            erros.append('Nome inválido ou muito curto')
        
        if cpf and not validar_cpf(cpf):
            erros.append('CPF inválido')
        
        if email and not validar_email(email):
            erros.append('Email inválido')
        
        # Verificar duplicidade no banco
        if cpf:
            count = await db.alunos.count_documents({"cpf": cpf})
            if count > 0:
                erros.append('CPF já cadastrado')
        
        valido = len(erros) == 0 and nome
        
        if valido:
            linhas_validas += 1
        else:
            linhas_com_erro += 1
        
        preview.append(AlunoPreview(
            linha=linha_num,
            nome=formatar_nome(nome) if nome else '',
            cpf=cpf,
            email=email.lower() if email else '',
            telefone=telefone,
            valido=valido,
            erros=erros
        ))
    
    return ValidacaoResult(
        sucesso=linhas_com_erro == 0 and linhas_validas > 0,
        total_linhas=len(df),
        linhas_validas=linhas_validas,
        linhas_com_erro=linhas_com_erro,
        preview=preview[:100]  # Limitar preview a 100 linhas
    )


@router.post("/executar", response_model=ImportacaoResult)
async def executar_importacao(
    file: UploadFile = File(...),
    curso_id: str = Query(..., description="ID do curso"),
    curso_nome: str = Query(..., description="Nome do curso"),
    projeto_id: Optional[str] = Query(None, description="ID do projeto"),
    projeto_nome: Optional[str] = Query(None, description="Nome do projeto"),
    empresa_id: Optional[str] = Query(None, description="ID da empresa"),
    empresa_nome: Optional[str] = Query(None, description="Nome da empresa"),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Executa importação de alunos criando pedidos de matrícula
    """
    # Ler arquivo
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar colunas
    df.columns = [col.upper().strip() for col in df.columns]
    
    column_mapping = {
        'ALUNO': 'NOME',
        'NOME COMPLETO': 'NOME',
        'NOME_COMPLETO': 'NOME',
        'E-MAIL': 'EMAIL',
        'E_MAIL': 'EMAIL',
        'TELEFONE1': 'TELEFONE',
        'TELEFONE 1': 'TELEFONE',
        'CEP': 'ENDERECO_CEP',
        'LOGRADOURO': 'ENDERECO_LOGRADOURO',
        'NUMERO': 'ENDERECO_NUMERO',
        'COMPLEMENTO': 'ENDERECO_COMPLEMENTO',
        'BAIRRO': 'ENDERECO_BAIRRO',
        'CIDADE': 'ENDERECO_CIDADE',
        'UF': 'ENDERECO_UF',
        'ESTADO': 'ENDERECO_UF'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Buscar próximo número de protocolo
    ano = datetime.now().year
    prefixo = f"CM-{ano}-"
    last = await db.pedidos.find(
        {"numero_protocolo": {"$regex": f"^{prefixo}"}},
        {"numero_protocolo": 1, "_id": 0}
    ).sort("numero_protocolo", -1).limit(1).to_list(1)
    if last:
        try:
            contador = int(last[0]["numero_protocolo"].split("-")[-1])
        except (ValueError, IndexError):
            contador = 0
    else:
        contador = await db.pedidos.count_documents({})

    pedidos_criados = 0
    alunos_importados = 0
    erros = []
    now = datetime.now(timezone.utc).isoformat()
    
    for idx, row in df.iterrows():
        linha_num = idx + 2
        
        try:
            nome = str(row.get('NOME', '')).strip() if pd.notna(row.get('NOME')) else ''
            
            if not nome or len(nome) < 3:
                erros.append(ErroImportacao(linha=linha_num, erro="Nome inválido"))
                continue
            
            cpf = limpar_cpf(row.get('CPF', ''))
            email = str(row.get('EMAIL', '')).strip().lower() if pd.notna(row.get('EMAIL')) else 'nao.informado@importacao.com'
            telefone = limpar_telefone(row.get('TELEFONE', '')) or 'N/A'
            
            # Verificar duplicidade
            if cpf:
                count = await db.alunos.count_documents({"cpf": cpf})
                if count > 0:
                    erros.append(ErroImportacao(linha=linha_num, erro="CPF já cadastrado"))
                    continue
            else:
                cpf = f"IMP{contador + pedidos_criados + 1:08d}"
            
            # Criar pedido
            contador += 1
            pedido_id = str(uuid.uuid4())
            protocolo = f"{prefixo}{contador:04d}"
            
            pedido_doc = {
                "id": pedido_id, "numero_protocolo": protocolo,
                "consultor_id": current_user.id, "consultor_nome": current_user.nome,
                "curso_id": curso_id, "curso_nome": curso_nome,
                "projeto_id": projeto_id, "projeto_nome": projeto_nome,
                "empresa_id": empresa_id, "empresa_nome": empresa_nome,
                "status": "pendente",
                "observacoes": f"Importado via planilha Excel em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "prioridade": "normal",
                "motivo_rejeicao": None, "data_exportacao": None, "exportado_por": None,
                "responsavel_id": None, "responsavel_nome": None,
                "created_at": now, "updated_at": now
            }
            await db.pedidos.insert_one(pedido_doc)
            
            # Criar aluno
            data_nasc = '2000-01-01'
            if 'DATA_NASCIMENTO' in df.columns and pd.notna(row.get('DATA_NASCIMENTO')):
                try:
                    data_nasc = pd.to_datetime(row['DATA_NASCIMENTO']).strftime('%Y-%m-%d')
                except Exception:
                    pass
            
            rg = str(row.get('RG', 'IMPORTADO')).strip() if pd.notna(row.get('RG')) else 'IMPORTADO'
            rg_orgao = str(row.get('RG_ORGAO', 'SSP')).strip() if pd.notna(row.get('RG_ORGAO')) else 'SSP'
            rg_uf = str(row.get('RG_UF', 'BA')).strip()[:2] if pd.notna(row.get('RG_UF')) else 'BA'
            
            aluno_doc = {
                "id": str(uuid.uuid4()), "pedido_id": pedido_id,
                "nome": formatar_nome(nome), "cpf": cpf, "email": email,
                "telefone": telefone, "data_nascimento": data_nasc,
                "rg": rg, "rg_orgao_emissor": rg_orgao, "rg_uf": rg_uf,
                "endereco_cep": str(row.get('ENDERECO_CEP', '00000000')).strip() if pd.notna(row.get('ENDERECO_CEP')) else '00000000',
                "endereco_logradouro": str(row.get('ENDERECO_LOGRADOURO', 'N/A')).strip() if pd.notna(row.get('ENDERECO_LOGRADOURO')) else 'N/A',
                "endereco_numero": str(row.get('ENDERECO_NUMERO', 'S/N')).strip() if pd.notna(row.get('ENDERECO_NUMERO')) else 'S/N',
                "endereco_complemento": str(row.get('ENDERECO_COMPLEMENTO', '')).strip() if pd.notna(row.get('ENDERECO_COMPLEMENTO')) else None,
                "endereco_bairro": str(row.get('ENDERECO_BAIRRO', 'N/A')).strip() if pd.notna(row.get('ENDERECO_BAIRRO')) else 'N/A',
                "endereco_cidade": str(row.get('ENDERECO_CIDADE', 'Salvador')).strip() if pd.notna(row.get('ENDERECO_CIDADE')) else 'Salvador',
                "endereco_uf": str(row.get('ENDERECO_UF', 'BA')).strip()[:2] if pd.notna(row.get('ENDERECO_UF')) else 'BA',
                "created_at": now, "updated_at": now
            }
            await db.alunos.insert_one(aluno_doc)
            
            pedidos_criados += 1
            alunos_importados += 1
            
        except Exception as e:
            erros.append(ErroImportacao(linha=linha_num, erro=str(e)))
    
    return ImportacaoResult(
        pedidos_criados=pedidos_criados,
        alunos_importados=alunos_importados,
        erros=erros
    )
