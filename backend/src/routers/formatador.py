"""
Router para processamento de planilhas de matrícula
Recebe planilha da empresa e retorna formatada/validada
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict
import pandas as pd
import io
from datetime import datetime

from src.services.formatador_planilha import FormatadorPlanilha, processar_linha_aluno

router = APIRouter(prefix="/formatador", tags=["Formatador de Planilhas"])


def detectar_cabecalho(df: pd.DataFrame) -> int:
    """Detecta a linha onde está o cabeçalho dos dados"""
    for i, row in df.iterrows():
        # Procura por colunas típicas de dados de aluno
        row_str = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
        if 'nome' in row_str and ('cpf' in row_str or 'aluno' in row_str):
            return i
    return 0


def mapear_colunas(df: pd.DataFrame) -> Dict[str, int]:
    """Mapeia nomes de colunas para índices"""
    mapeamento = {}
    
    # Mapeamento baseado na estrutura conhecida das planilhas do SENAI
    # Índices são os números das colunas (0-indexed)
    mapeamento_fixo = {
        'nome': 1,
        'email': 2,
        'cpf': 3,
        'telefone': 4,
        'funcao': 5,
        'rg': 6,
        'data_emissao_rg': 7,
        'orgao_emissor': 8,
        'naturalidade': 9,
        'data_nascimento': 10,
        'nome_pai': 11,
        'nome_mae': 12,
        'endereco': 13,
        'numero': 14,
        'bairro': 15,
        'cep': 16,
        'resp_nome': 17,
        'resp_rg': 18,
        'resp_data_rg': 19,
        'resp_cpf': 20,
        'resp_nascimento': 21,
    }
    
    # Tentar detectar dinamicamente baseado nos nomes das colunas
    colunas_esperadas = {
        'nome': ['nome completo', 'nome do aluno', 'nome'],
        'email': ['email', 'e-mail'],
        'cpf': ['cpf'],
        'telefone': ['telefone', 'telefones', 'celular'],
        'funcao': ['função', 'funcao', 'cargo'],
        'rg': ['rg'],
        'data_emissao_rg': ['data de emissão', 'data emissão rg', 'emissão rg', 'emissão'],
        'orgao_emissor': ['orgão emissor', 'orgao emissor', 'emissor'],
        'naturalidade': ['naturalidade'],
        'data_nascimento': ['data de nascimento', 'nascimento', 'dt nascimento'],
        'nome_pai': ['nome do pai', 'pai'],
        'nome_mae': ['nome da mãe', 'nome mae', 'mãe', 'mae'],
        'endereco': ['endereço', 'endereco', 'rua'],
        'numero': ['número', 'numero', 'nº'],
        'bairro': ['bairro'],
        'cep': ['cep'],
        'resp_nome': ['nome (mãe / pai / tutor', 'responsável', 'nome responsável', 'tutor'],
        'resp_rg': ['rg do responsável', 'rg responsável'],
        'resp_data_rg': ['data de exp. do rg do responsável', 'data rg responsável', 'exp. do rg'],
        'resp_cpf': ['cpf do responsável', 'cpf responsável'],
        'resp_nascimento': ['data de nascimento do responsável', 'nasc responsável'],
    }
    
    # Primeiro tentar mapeamento dinâmico
    for col_idx, col_name in enumerate(df.columns):
        if pd.isna(col_name):
            continue
        col_lower = str(col_name).lower().strip()
        for campo, variantes in colunas_esperadas.items():
            for variante in variantes:
                if variante in col_lower:
                    if campo not in mapeamento:  # Não sobrescrever
                        mapeamento[campo] = col_idx
                    break
    
    # Se não conseguiu mapear campos essenciais, usar mapeamento fixo
    campos_essenciais = ['nome', 'cpf', 'email', 'telefone']
    if not all(c in mapeamento for c in campos_essenciais):
        return mapeamento_fixo
    
    return mapeamento


@router.post("/processar")
async def processar_planilha(arquivo: UploadFile = File(...)):
    """
    Processa planilha de matrícula e retorna dados formatados
    
    Aceita: .xls, .xlsx
    
    Retorna JSON com:
    - empresa: dados da empresa
    - alunos: lista de alunos com dados originais e formatados
    - resumo: contagem de OK, ERRO, AVISO
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not arquivo.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo não fornecido")
    
    filename_lower = arquivo.filename.lower()
    if not filename_lower.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xls ou .xlsx)")
    
    try:
        conteudo = await arquivo.read()
        if not conteudo:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        logger.info(f"Processando arquivo: {arquivo.filename}, tamanho: {len(conteudo)} bytes")
        
        # Detectar engine baseado na extensão
        if filename_lower.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='xlrd')
        else:
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='openpyxl')
        
        logger.info(f"Planilha lida com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {arquivo.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Detectar cabeçalho
    linha_cabecalho = detectar_cabecalho(df)
    
    # Pegar info da empresa (linhas antes do cabeçalho)
    empresa_info = {}
    for i in range(linha_cabecalho):
        row = df.iloc[i]
        for j, val in enumerate(row):
            if pd.notna(val):
                val_str = str(val).strip()
                if 'empresa:' in val_str.lower():
                    # Próximo valor não-vazio é o nome da empresa
                    for k in range(j+1, len(row)):
                        if pd.notna(row.iloc[k]):
                            empresa_info['nome'] = str(row.iloc[k]).strip()
                            break
                elif 'responsável' in val_str.lower() and 'empresa' in val_str.lower():
                    for k in range(j+1, len(row)):
                        if pd.notna(row.iloc[k]):
                            empresa_info['responsavel'] = str(row.iloc[k]).strip()
                            break
                elif 'telefone' in val_str.lower() and 'responsável' in val_str.lower():
                    for k in range(j+1, len(row)):
                        if pd.notna(row.iloc[k]):
                            tel_fmt, _, _ = FormatadorPlanilha.formatar_telefone(str(row.iloc[k]))
                            empresa_info['telefone'] = tel_fmt
                            break
    
    # Renomear colunas com o cabeçalho detectado
    df.columns = df.iloc[linha_cabecalho]
    df = df.iloc[linha_cabecalho + 1:].reset_index(drop=True)
    
    # Mapear colunas
    col_map = mapear_colunas(df)
    
    # Processar cada aluno
    alunos = []
    resumo = {'ok': 0, 'erro': 0, 'aviso': 0}
    
    for idx, row in df.iterrows():
        # Pular linhas vazias
        if pd.isna(row.iloc[1]) if len(row) > 1 else True:
            continue
        
        # Extrair dados
        dados = {}
        for campo, col_idx in col_map.items():
            if col_idx < len(row):
                val = row.iloc[col_idx]
                dados[campo] = val if pd.notna(val) else None
        
        if not dados.get('nome'):
            continue
        
        # Processar
        resultado = processar_linha_aluno(dados)
        resultado['linha'] = idx + linha_cabecalho + 2  # +2 para Excel (1-indexed + header)
        alunos.append(resultado)
        
        # Contabilizar
        if resultado['status'] == 'OK':
            resumo['ok'] += 1
        elif resultado['status'] == 'ERRO':
            resumo['erro'] += 1
        else:
            resumo['aviso'] += 1
    
    return {
        "arquivo": arquivo.filename,
        "empresa": empresa_info,
        "alunos": alunos,
        "resumo": resumo,
        "total": len(alunos),
        "processado_em": datetime.now().isoformat()
    }


@router.post("/processar-e-baixar")
async def processar_e_baixar(arquivo: UploadFile = File(...)):
    """
    Processa planilha e retorna nova planilha Excel formatada
    """
    if not arquivo.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xls ou .xlsx)")
    
    try:
        conteudo = await arquivo.read()
        
        if arquivo.filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='xlrd')
        else:
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='openpyxl')
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Detectar cabeçalho
    linha_cabecalho = detectar_cabecalho(df)
    
    # Renomear e processar
    df.columns = df.iloc[linha_cabecalho]
    df_dados = df.iloc[linha_cabecalho + 1:].reset_index(drop=True)
    col_map = mapear_colunas(df_dados)
    
    # Criar DataFrame de saída
    saida_dados = []
    
    for idx, row in df_dados.iterrows():
        if pd.isna(row.iloc[1]) if len(row) > 1 else True:
            continue
        
        dados = {}
        for campo, col_idx in col_map.items():
            if col_idx < len(row):
                val = row.iloc[col_idx]
                dados[campo] = val if pd.notna(val) else None
        
        if not dados.get('nome'):
            continue
        
        resultado = processar_linha_aluno(dados)
        fmt = resultado['formatado']
        
        saida_dados.append({
            'STATUS': resultado['status'],
            'ERROS': '; '.join(resultado['erros']) if resultado['erros'] else '',
            'AVISOS': '; '.join(resultado['avisos']) if resultado['avisos'] else '',
            'NOME': fmt.get('nome', ''),
            'EMAIL': fmt.get('email', ''),
            'CPF': fmt.get('cpf', ''),
            'TELEFONE': fmt.get('telefone', ''),
            'FUNÇÃO': fmt.get('funcao', ''),
            'RG': fmt.get('rg', ''),
            'DATA EMISSÃO RG': fmt.get('data_emissao_rg', ''),
            'ÓRGÃO EMISSOR': fmt.get('orgao_emissor', ''),
            'NATURALIDADE': fmt.get('naturalidade', ''),
            'DATA NASCIMENTO': fmt.get('data_nascimento', ''),
            'NOME PAI': fmt.get('nome_pai', ''),
            'NOME MÃE': fmt.get('nome_mae', ''),
            'ENDEREÇO': fmt.get('endereco', ''),
            'NÚMERO': fmt.get('numero', ''),
            'BAIRRO': fmt.get('bairro', ''),
            'CEP': fmt.get('cep', ''),
            'RESPONSÁVEL NOME': fmt.get('resp_nome', ''),
            'RESPONSÁVEL CPF': fmt.get('resp_cpf', ''),
            'RESPONSÁVEL RG': fmt.get('resp_rg', ''),
            'RESPONSÁVEL DATA RG': fmt.get('resp_data_rg', ''),
            'RESPONSÁVEL NASCIMENTO': fmt.get('resp_nascimento', ''),
        })
    
    df_saida = pd.DataFrame(saida_dados)
    
    # Gerar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_saida.to_excel(writer, index=False, sheet_name='Dados Formatados')
        
        # Ajustar largura das colunas
        worksheet = writer.sheets['Dados Formatados']
        for i, col in enumerate(df_saida.columns):
            max_len = max(df_saida[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + i) if i < 26 else 'A' + chr(65 + i - 26)].width = min(max_len, 50)
    
    output.seek(0)
    
    nome_saida = arquivo.filename.replace('.xls', '_FORMATADO.xlsx')
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nome_saida}"}
    )


# Endpoints auxiliares

@router.post("/validar-cpf")
async def validar_cpf(cpf: str):
    """Valida um CPF específico"""
    fmt, ok, msg = FormatadorPlanilha.formatar_cpf(cpf)
    return {"cpf_original": cpf, "cpf_formatado": fmt, "valido": ok, "mensagem": msg}


@router.post("/formatar-nome")
async def formatar_nome(nome: str):
    """Formata um nome específico"""
    fmt, ok, msg = FormatadorPlanilha.formatar_nome(nome)
    return {"nome_original": nome, "nome_formatado": fmt, "valido": ok, "mensagem": msg}


@router.post("/formatar-telefone")
async def formatar_telefone(telefone: str):
    """Formata um telefone específico"""
    fmt, ok, msg = FormatadorPlanilha.formatar_telefone(telefone)
    return {"telefone_original": telefone, "telefone_formatado": fmt, "valido": ok, "mensagem": msg}
