"""
Router para processamento de planilhas de matrícula
Recebe planilha da empresa e retorna formatada/validada
Padrão BMP (Brasil Mais Produtivo) com correção ortográfica
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import pandas as pd
import io
import re
from datetime import datetime
import logging

from src.services.formatador_planilha import FormatadorPlanilha, processar_linha_aluno
from src.services.formatador_bmp import FormatadorBMP

router = APIRouter(prefix="/formatador", tags=["Formatador de Planilhas"])
logger = logging.getLogger(__name__)


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
        
        logger.info(f"Processando para download: {arquivo.filename}, tamanho: {len(conteudo)} bytes")
        
        if filename_lower.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='xlrd')
        else:
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='openpyxl')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ler arquivo para download {arquivo.filename}: {str(e)}")
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


@router.post("/processar-para-totvs")
async def processar_para_totvs(arquivo: UploadFile = File(...)):
    """
    Processa planilha de entrada e gera saída no formato TEMPLATE TOTVS
    
    Formato de saída (ordem das colunas TOTVS):
    CPF, RG, EMISSÃO, ÓRGÃO EMISSOR, ESTADO EMISSOR, NOME COMPLETO DO ALUNO,
    ESTADO NATAL DO ALUNO, NATURALIDADE DO ALUNO, DATA DE NASCIMENTO DO ALUNO,
    SEXO, E-MAIL PESSOAL DO ALUNO, COR/RAÇA, CEP, ENDEREÇO, NÚMERO, COMPLEMENTO,
    BAIRRO, ESTADO, CIDADE, PAÍS, TELEFONE, NOME COMPLETO DO PAI, ESTADO NATAL,
    NATURALIDADE, DATA DE NASCIMENTO, SEXO, E-MAIL, NOME COMPLETO DA MÃE,
    ESTADO NATAL, NATURALIDADE, DATA DE NASCIMENTO, SEXO, E-MAIL
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
        
        logger.info(f"Processando para TOTVS: {arquivo.filename}, tamanho: {len(conteudo)} bytes")
        
        if filename_lower.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='xlrd')
        else:
            df = pd.read_excel(io.BytesIO(conteudo), header=None, engine='openpyxl')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ler arquivo para TOTVS {arquivo.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Detectar cabeçalho
    linha_cabecalho = detectar_cabecalho(df)
    
    # Renomear e processar
    df.columns = df.iloc[linha_cabecalho]
    df_dados = df.iloc[linha_cabecalho + 1:].reset_index(drop=True)
    col_map = mapear_colunas_totvs(df_dados)
    
    # Formatador BMP
    formatador = FormatadorBMP()
    
    # Criar DataFrame de saída no formato TOTVS
    saida_dados = []
    auditoria = {
        'total_linhas': 0,
        'nomes_padronizados': 0,
        'cpfs_validos': 0,
        'cpfs_invalidos': 0,
        'ceps_formatados': 0,
        'telefones_formatados': 0,
        'emails_ajustados': 0,
        'correcoes_ortograficas': 0,
        'pendencias': []
    }
    
    for idx, row in df_dados.iterrows():
        # Pular linhas vazias
        if all(pd.isna(row.iloc[i]) if i < len(row) else True for i in range(min(5, len(row)))):
            continue
        
        auditoria['total_linhas'] += 1
        
        # Extrair dados usando mapeamento flexível
        dados = extrair_dados_flexivel(row, col_map, df_dados.columns)
        
        if not dados.get('nome'):
            continue
        
        # Processar cada campo
        registro_totvs = processar_para_template_totvs(dados, formatador, auditoria)
        saida_dados.append(registro_totvs)
    
    # Criar DataFrame com colunas do template TOTVS (na ordem exata)
    colunas_totvs = [
        'CPF', 'RG', 'EMISSÃO', 'ÓRGÃO EMISSOR', 'ESTADO EMISSOR',
        'NOME COMPLETO DO ALUNO', 'ESTADO NATAL DO ALUNO', 'NATURALIDADE DO ALUNO',
        'DATA DE NASCIMENTO DO ALUNO', 'SEXO', 'E-MAIL PESSOAL DO ALUNO', 'COR/RAÇA',
        'CEP', 'ENDEREÇO', 'NÚMERO', 'COMPLEMENTO', 'BAIRRO', 'ESTADO', 'CIDADE', 'PAÍS',
        'TELEFONE', 'NOME COMPLETO DO PAI', 'ESTADO NATAL', 'NATURALIDADE',
        'DATA DE NASCIMENTO', 'SEXO2', 'E-MAIL',
        'NOME COMPLETO DA MÃE', 'ESTADO NATAL3', 'NATURALIDADE4',
        'DATA DE NASCIMENTO5', 'SEXO6', 'E-MAIL7',
        '_STATUS', '_ERROS', '_AVISOS'
    ]
    
    df_saida = pd.DataFrame(saida_dados)
    
    # Reordenar colunas conforme template TOTVS
    colunas_disponiveis = [c for c in colunas_totvs if c in df_saida.columns]
    df_saida = df_saida[colunas_disponiveis]
    
    # Gerar Excel com duas abas
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba 1: Dados formatados para TOTVS
        df_saida.to_excel(writer, index=False, sheet_name='Template TOTVS')
        
        # Ajustar largura das colunas
        worksheet = writer.sheets['Template TOTVS']
        for i, col in enumerate(df_saida.columns):
            col_letter = get_column_letter(i + 1)
            max_len = max(df_saida[col].astype(str).apply(len).max(), len(str(col))) + 2
            worksheet.column_dimensions[col_letter].width = min(max_len, 40)
        
        # Aba 2: Auditoria
        auditoria_df = pd.DataFrame([{
            'Métrica': 'Total de linhas processadas',
            'Valor': auditoria['total_linhas']
        }, {
            'Métrica': 'Nomes padronizados',
            'Valor': auditoria['nomes_padronizados']
        }, {
            'Métrica': 'CPFs válidos',
            'Valor': auditoria['cpfs_validos']
        }, {
            'Métrica': 'CPFs inválidos',
            'Valor': auditoria['cpfs_invalidos']
        }, {
            'Métrica': 'CEPs formatados',
            'Valor': auditoria['ceps_formatados']
        }, {
            'Métrica': 'Telefones formatados',
            'Valor': auditoria['telefones_formatados']
        }, {
            'Métrica': 'E-mails ajustados',
            'Valor': auditoria['emails_ajustados']
        }, {
            'Métrica': 'Correções ortográficas',
            'Valor': auditoria['correcoes_ortograficas']
        }])
        auditoria_df.to_excel(writer, index=False, sheet_name='Auditoria')
        
        # Se houver pendências, adicionar
        if auditoria['pendencias']:
            pendencias_df = pd.DataFrame(auditoria['pendencias'])
            pendencias_df.to_excel(writer, index=False, sheet_name='Pendências Validação')
    
    output.seek(0)
    
    nome_saida = arquivo.filename.replace('.xls', '').replace('.xlsx', '') + '_TOTVS.xlsx'
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nome_saida}"}
    )


def get_column_letter(col_idx: int) -> str:
    """Converte índice de coluna (1-based) para letra Excel"""
    result = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def mapear_colunas_totvs(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Mapeia colunas da planilha de entrada para campos do template TOTVS
    Retorna um dicionário com listas de possíveis nomes de colunas
    """
    return {
        # Dados do aluno
        'cpf': ['cpf', 'cpf do aluno', 'cpf aluno'],
        'rg': ['rg', 'rg do aluno', 'rg aluno'],
        'emissao_rg': ['emissão', 'data de emissão', 'data emissão rg', 'emissao', 'data de emissão (rg) do aluno'],
        'orgao_emissor': ['órgão emissor', 'orgao emissor', 'emissor', 'emissor rg do aluno', 'orgão'],
        'estado_emissor': ['estado emissor', 'uf emissor', 'uf emissor rg do aluno'],
        'nome': ['nome completo do aluno', 'nome completo', 'nome do aluno', 'nome', 'aluno'],
        'estado_natal': ['estado natal do aluno', 'estado natal', 'uf nascimento', 'uf'],
        'naturalidade': ['naturalidade do aluno', 'naturalidade', 'naturalidade aluno', 'cidade nascimento'],
        'data_nascimento': ['data de nascimento do aluno', 'data de nascimento', 'data nascimento', 'nascimento', 'dt nascimento'],
        'sexo': ['sexo', 'gênero', 'genero'],
        'email': ['e-mail pessoal do aluno', 'e-mail do aluno', 'email do aluno', 'e-mail', 'email', 'e-mail aluno'],
        'cor_raca': ['cor/raça', 'cor', 'raça', 'cor raca'],
        'cep': ['cep'],
        'endereco': ['endereço', 'endereco', 'end. do aluno', 'logradouro', 'rua'],
        'numero': ['número', 'numero', 'nº', 'num'],
        'complemento': ['complemento', 'compl'],
        'bairro': ['bairro'],
        'estado': ['estado', 'uf'],
        'cidade': ['cidade', 'município', 'municipio'],
        'pais': ['país', 'pais'],
        'telefone': ['telefone', 'telefones', 'telefone aluno', 'celular', 'tel'],
        
        # Dados do pai
        'pai_nome': ['nome completo do pai', 'nome do pai', 'pai', 'pai nome'],
        'pai_estado_natal': ['estado natal pai', 'pai uf nascimento pai'],
        'pai_naturalidade': ['naturalidade pai', 'pai cidade nascimento pai'],
        'pai_data_nascimento': ['data de nascimento pai', 'pai data de nascimento pai'],
        'pai_email': ['e-mail pai', 'pai e-mail pai'],
        'pai_cpf': ['cpf do pai', 'pai cpf pai'],
        
        # Dados da mãe
        'mae_nome': ['nome completo da mãe', 'nome da mãe', 'nome mae', 'mãe', 'mae'],
        'mae_estado_natal': ['estado natal mãe', 'mae uf nascimento mae', 'mãe uf nascimento mãe'],
        'mae_naturalidade': ['naturalidade mãe', 'mae cidade nascimento mae', 'mãe cidade nascimento mãe'],
        'mae_data_nascimento': ['data de nascimento mãe', 'mae data de nascimento mae', 'mãe data de nascimento mãe'],
        'mae_email': ['e-mail mãe', 'mae e-mail mae', 'mãe e-mail mãe'],
        'mae_cpf': ['cpf da mãe', 'mae cpf mae', 'mãe cpf mãe'],
        
        # Responsável (tutor legal)
        'resp_nome': ['nome (mãe / pai / tutor', 'responsável', 'nome responsável', 'tutor'],
        'resp_rg': ['rg do responsável', 'rg responsável'],
        'resp_data_rg': ['data de exp. do rg do responsável', 'data rg responsável'],
        'resp_cpf': ['cpf do responsável', 'cpf responsável'],
        'resp_nascimento': ['data de nascimento do responsável', 'nasc responsável'],
    }


def extrair_dados_flexivel(row: pd.Series, col_map: Dict, colunas: pd.Index) -> Dict:
    """
    Extrai dados da linha usando mapeamento flexível de colunas
    """
    dados = {}
    colunas_lower = {str(c).lower().strip(): i for i, c in enumerate(colunas) if pd.notna(c)}
    
    for campo, variantes in col_map.items():
        for variante in variantes:
            variante_lower = variante.lower()
            for col_name, col_idx in colunas_lower.items():
                if variante_lower in col_name or col_name in variante_lower:
                    if col_idx < len(row):
                        val = row.iloc[col_idx]
                        if pd.notna(val) and str(val).strip():
                            dados[campo] = val
                            break
            if campo in dados:
                break
    
    return dados


def processar_para_template_totvs(dados: Dict, formatador: FormatadorBMP, auditoria: Dict) -> Dict:
    """
    Processa dados extraídos e retorna no formato do template TOTVS
    """
    erros = []
    avisos = []
    
    registro = {}
    
    # === ALUNO ===
    
    # CPF
    cpf_raw = str(dados.get('cpf', '')).strip()
    if cpf_raw:
        cpf_fmt, cpf_ok, cpf_msg = formatador.validar_cpf(cpf_raw)
        registro['CPF'] = cpf_fmt
        if cpf_ok:
            auditoria['cpfs_validos'] += 1
        else:
            auditoria['cpfs_invalidos'] += 1
            erros.append(f"CPF: {cpf_msg}")
    else:
        registro['CPF'] = ''
    
    # RG (apenas números)
    rg_raw = str(dados.get('rg', '')).strip()
    registro['RG'] = re.sub(r'\D', '', rg_raw) if rg_raw else ''
    
    # Emissão RG
    emissao_raw = dados.get('emissao_rg', '')
    if emissao_raw:
        emissao_fmt, _, _ = formatador.formatar_data(str(emissao_raw))
        registro['EMISSÃO'] = emissao_fmt
    else:
        registro['EMISSÃO'] = ''
    
    # Órgão Emissor (uppercase)
    orgao_raw = str(dados.get('orgao_emissor', '')).strip()
    registro['ÓRGÃO EMISSOR'] = orgao_raw.upper() if orgao_raw else ''
    
    # Estado Emissor
    estado_emissor_raw = str(dados.get('estado_emissor', '')).strip()
    registro['ESTADO EMISSOR'] = estado_emissor_raw.upper() if estado_emissor_raw else 'BA'
    
    # Nome do Aluno
    nome_raw = str(dados.get('nome', '')).strip()
    if nome_raw:
        nome_fmt, meta = formatador.formatar_nome(nome_raw)
        registro['NOME COMPLETO DO ALUNO'] = nome_fmt
        if meta.get('modificado'):
            auditoria['nomes_padronizados'] += 1
        if meta.get('correcoes_ortograficas', 0) > 0:
            auditoria['correcoes_ortograficas'] += meta['correcoes_ortograficas']
    else:
        registro['NOME COMPLETO DO ALUNO'] = ''
    
    # Estado Natal do Aluno
    estado_natal_raw = str(dados.get('estado_natal', '')).strip()
    registro['ESTADO NATAL DO ALUNO'] = estado_natal_raw.upper() if estado_natal_raw else 'BA'
    
    # Naturalidade do Aluno
    naturalidade_raw = str(dados.get('naturalidade', '')).strip()
    if naturalidade_raw:
        nat_fmt, _ = formatador.formatar_endereco(naturalidade_raw)
        registro['NATURALIDADE DO ALUNO'] = nat_fmt
    else:
        registro['NATURALIDADE DO ALUNO'] = ''
    
    # Data de Nascimento do Aluno
    nasc_raw = dados.get('data_nascimento', '')
    if nasc_raw:
        nasc_fmt, nasc_ok, _ = formatador.formatar_data(str(nasc_raw))
        registro['DATA DE NASCIMENTO DO ALUNO'] = nasc_fmt
        if not nasc_ok and nasc_raw:
            avisos.append("Data nascimento em formato não reconhecido")
    else:
        registro['DATA DE NASCIMENTO DO ALUNO'] = ''
    
    # Sexo
    sexo_raw = str(dados.get('sexo', '')).strip().upper()
    if sexo_raw in ['M', 'MASCULINO', 'MASC']:
        registro['SEXO'] = 'M'
    elif sexo_raw in ['F', 'FEMININO', 'FEM']:
        registro['SEXO'] = 'F'
    else:
        registro['SEXO'] = sexo_raw[:1] if sexo_raw else ''
    
    # Email do Aluno
    email_raw = str(dados.get('email', '')).strip()
    if email_raw:
        email_fmt, email_ok, _ = formatador.formatar_email(email_raw)
        registro['E-MAIL PESSOAL DO ALUNO'] = email_fmt
        if email_ok:
            auditoria['emails_ajustados'] += 1
    else:
        registro['E-MAIL PESSOAL DO ALUNO'] = ''
    
    # Cor/Raça
    registro['COR/RAÇA'] = str(dados.get('cor_raca', '')).strip().title()
    
    # CEP
    cep_raw = str(dados.get('cep', '')).strip()
    if cep_raw:
        cep_fmt, cep_ok, _ = formatador.formatar_cep(cep_raw)
        registro['CEP'] = cep_fmt
        if cep_ok:
            auditoria['ceps_formatados'] += 1
    else:
        registro['CEP'] = ''
    
    # Endereço
    endereco_raw = str(dados.get('endereco', '')).strip()
    if endereco_raw:
        end_fmt, _ = formatador.formatar_endereco(endereco_raw)
        registro['ENDEREÇO'] = end_fmt
    else:
        registro['ENDEREÇO'] = ''
    
    # Número
    registro['NÚMERO'] = str(dados.get('numero', '')).strip()
    
    # Complemento
    registro['COMPLEMENTO'] = str(dados.get('complemento', '')).strip()
    
    # Bairro
    bairro_raw = str(dados.get('bairro', '')).strip()
    if bairro_raw:
        bairro_fmt, _ = formatador.formatar_endereco(bairro_raw)
        registro['BAIRRO'] = bairro_fmt
    else:
        registro['BAIRRO'] = ''
    
    # Estado
    estado_raw = str(dados.get('estado', '')).strip()
    registro['ESTADO'] = estado_raw.upper() if estado_raw else 'BA'
    
    # Cidade
    cidade_raw = str(dados.get('cidade', '')).strip()
    if cidade_raw:
        cidade_fmt, _ = formatador.formatar_endereco(cidade_raw)
        registro['CIDADE'] = cidade_fmt
    else:
        registro['CIDADE'] = ''
    
    # País
    pais_raw = str(dados.get('pais', '')).strip()
    registro['PAÍS'] = pais_raw.title() if pais_raw else 'Brasil'
    
    # Telefone
    telefone_raw = str(dados.get('telefone', '')).strip()
    if telefone_raw:
        tel_fmt, tel_ok, _ = formatador.formatar_telefone(telefone_raw)
        registro['TELEFONE'] = tel_fmt
        if tel_ok:
            auditoria['telefones_formatados'] += 1
    else:
        registro['TELEFONE'] = ''
    
    # === PAI ===
    pai_nome_raw = str(dados.get('pai_nome', '')).strip()
    if pai_nome_raw:
        pai_nome_fmt, _ = formatador.formatar_nome(pai_nome_raw)
        registro['NOME COMPLETO DO PAI'] = pai_nome_fmt
    else:
        registro['NOME COMPLETO DO PAI'] = ''
    
    registro['ESTADO NATAL'] = str(dados.get('pai_estado_natal', '')).strip().upper() or ''
    
    pai_nat_raw = str(dados.get('pai_naturalidade', '')).strip()
    if pai_nat_raw:
        pai_nat_fmt, _ = formatador.formatar_endereco(pai_nat_raw)
        registro['NATURALIDADE'] = pai_nat_fmt
    else:
        registro['NATURALIDADE'] = ''
    
    pai_nasc_raw = dados.get('pai_data_nascimento', '')
    if pai_nasc_raw:
        pai_nasc_fmt, _, _ = formatador.formatar_data(str(pai_nasc_raw))
        registro['DATA DE NASCIMENTO'] = pai_nasc_fmt
    else:
        registro['DATA DE NASCIMENTO'] = ''
    
    registro['SEXO2'] = 'M'  # Pai é sempre masculino
    
    pai_email_raw = str(dados.get('pai_email', '')).strip()
    if pai_email_raw:
        pai_email_fmt, _, _ = formatador.formatar_email(pai_email_raw)
        registro['E-MAIL'] = pai_email_fmt
    else:
        registro['E-MAIL'] = ''
    
    # === MÃE ===
    mae_nome_raw = str(dados.get('mae_nome', '')).strip()
    if mae_nome_raw:
        mae_nome_fmt, _ = formatador.formatar_nome(mae_nome_raw)
        registro['NOME COMPLETO DA MÃE'] = mae_nome_fmt
    else:
        registro['NOME COMPLETO DA MÃE'] = ''
    
    registro['ESTADO NATAL3'] = str(dados.get('mae_estado_natal', '')).strip().upper() or ''
    
    mae_nat_raw = str(dados.get('mae_naturalidade', '')).strip()
    if mae_nat_raw:
        mae_nat_fmt, _ = formatador.formatar_endereco(mae_nat_raw)
        registro['NATURALIDADE4'] = mae_nat_fmt
    else:
        registro['NATURALIDADE4'] = ''
    
    mae_nasc_raw = dados.get('mae_data_nascimento', '')
    if mae_nasc_raw:
        mae_nasc_fmt, _, _ = formatador.formatar_data(str(mae_nasc_raw))
        registro['DATA DE NASCIMENTO5'] = mae_nasc_fmt
    else:
        registro['DATA DE NASCIMENTO5'] = ''
    
    registro['SEXO6'] = 'F'  # Mãe é sempre feminino
    
    mae_email_raw = str(dados.get('mae_email', '')).strip()
    if mae_email_raw:
        mae_email_fmt, _, _ = formatador.formatar_email(mae_email_raw)
        registro['E-MAIL7'] = mae_email_fmt
    else:
        registro['E-MAIL7'] = ''
    
    # Status
    registro['_STATUS'] = 'ERRO' if erros else ('AVISO' if avisos else 'OK')
    registro['_ERROS'] = '; '.join(erros) if erros else ''
    registro['_AVISOS'] = '; '.join(avisos) if avisos else ''
    
    return registro


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
