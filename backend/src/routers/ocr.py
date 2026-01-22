"""Router de OCR - Extração de dados de documentos"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from PIL import Image
import pytesseract
import io
import re
from typing import Optional
from datetime import datetime

from src.domain.entities import Usuario
from .dependencies import get_current_user

router = APIRouter(prefix="/ocr", tags=["OCR"])


def extrair_cpf(texto: str) -> Optional[str]:
    """Extrai CPF do texto"""
    # Padrão: 000.000.000-00 ou 00000000000
    padrao = r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}'
    match = re.search(padrao, texto)
    if match:
        cpf = re.sub(r'\D', '', match.group())
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return None


def extrair_rg(texto: str) -> Optional[str]:
    """Extrai RG do texto"""
    # Padrões comuns de RG
    padroes = [
        r'\d{2}\.?\d{3}\.?\d{3}-?\d',  # 00.000.000-0
        r'\d{1,2}\.?\d{3}\.?\d{3}',     # 0.000.000 ou 00.000.000
    ]
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            return match.group()
    return None


def extrair_data_nascimento(texto: str) -> Optional[str]:
    """Extrai data de nascimento"""
    # Padrões: DD/MM/AAAA ou DD-MM-AAAA
    padroes = [
        r'(\d{2}[/\-]\d{2}[/\-]\d{4})',
        r'NASCIMENTO[:\s]*(\d{2}[/\-]\d{2}[/\-]\d{4})',
        r'DATA NASC[:\s]*(\d{2}[/\-]\d{2}[/\-]\d{4})',
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            data_str = match.group(1) if match.lastindex else match.group()
            data_str = data_str.replace('/', '-')
            partes = data_str.split('-')
            if len(partes) == 3:
                return f"{partes[2]}-{partes[1]}-{partes[0]}"  # YYYY-MM-DD
    return None


def extrair_nome(texto: str) -> Optional[str]:
    """Extrai nome do documento"""
    linhas = texto.split('\n')
    
    # Procurar após "NOME" ou linha com nome completo
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()
        
        # Se a linha contém "NOME", pegar a próxima ou a própria
        if 'NOME' in linha_upper and ':' in linha:
            nome = linha.split(':')[-1].strip()
            if len(nome) > 5:
                return nome.title()
        
        # Procurar linha que parece ser um nome (3+ palavras, só letras)
        palavras = linha.strip().split()
        if len(palavras) >= 3:
            eh_nome = all(p.isalpha() or p in ['DA', 'DE', 'DO', 'DAS', 'DOS'] for p in palavras)
            if eh_nome and len(linha.strip()) > 10:
                return linha.strip().title()
    
    return None


def extrair_nome_pai(texto: str) -> Optional[str]:
    """Extrai nome do pai"""
    padroes = [
        r'FILIA[CÇ][AÃ]O[:\s]*([A-Z\s]+)',
        r'PAI[:\s]*([A-Z\s]+)',
    ]
    for padrao in padroes:
        match = re.search(padrao, texto.upper())
        if match:
            nome = match.group(1).strip()
            # Limpar e formatar
            nome = re.sub(r'\s+', ' ', nome)
            if len(nome) > 5:
                return nome.title()
    return None


def extrair_nome_mae(texto: str) -> Optional[str]:
    """Extrai nome da mãe"""
    padroes = [
        r'M[AÃ]E[:\s]*([A-Z\s]+)',
        r'FILIA[CÇ][AÃ]O[:\s]*[A-Z\s]+\n([A-Z\s]+)',
    ]
    for padrao in padroes:
        match = re.search(padrao, texto.upper())
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\s+', ' ', nome)
            if len(nome) > 5:
                return nome.title()
    return None


def extrair_naturalidade(texto: str) -> Optional[str]:
    """Extrai cidade de nascimento"""
    padroes = [
        r'NATURALIDADE[:\s]*([A-Z\s]+)',
        r'NATURAL DE[:\s]*([A-Z\s]+)',
    ]
    for padrao in padroes:
        match = re.search(padrao, texto.upper())
        if match:
            cidade = match.group(1).strip().split('\n')[0]
            cidade = re.sub(r'\s+', ' ', cidade)
            return cidade.title()
    return None


def extrair_orgao_emissor(texto: str) -> Optional[str]:
    """Extrai órgão emissor do RG"""
    orgaos = ['SSP', 'DETRAN', 'PC', 'IFP', 'SESP', 'SDS', 'SEJUSP', 'POLITEC']
    texto_upper = texto.upper()
    
    for orgao in orgaos:
        if orgao in texto_upper:
            return orgao
    return None


def extrair_uf(texto: str) -> Optional[str]:
    """Extrai UF do documento"""
    ufs = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 
           'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 
           'SP', 'SE', 'TO']
    
    # Procurar UF no texto (geralmente aparece após SSP ou em contexto)
    for uf in ufs:
        # Padrão SSP/UF ou SSP-UF
        if re.search(rf'SSP[/\-\s]*{uf}', texto.upper()):
            return uf
        # Padrão UF isolado próximo de palavras-chave
        if re.search(rf'\b{uf}\b', texto.upper()):
            return uf
    
    return None


def detectar_tipo_documento(texto: str) -> str:
    """Detecta se é CNH, RG ou outro"""
    texto_upper = texto.upper()
    
    if 'CARTEIRA NACIONAL' in texto_upper or 'CNH' in texto_upper or 'HABILITAÇÃO' in texto_upper:
        return 'CNH'
    elif 'IDENTIDADE' in texto_upper or 'REGISTRO GERAL' in texto_upper:
        return 'RG'
    elif 'CERTIDÃO' in texto_upper or 'NASCIMENTO' in texto_upper:
        return 'CERTIDAO'
    
    return 'DESCONHECIDO'


@router.post("/extrair-documento")
async def extrair_dados_documento(
    arquivo: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Extrai dados de um documento (CNH, RG) usando OCR.
    Aceita imagens (JPG, PNG) e PDF.
    """
    # Validar tipo de arquivo
    tipos_aceitos = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    if arquivo.content_type not in tipos_aceitos:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de arquivo não suportado. Use: JPG, PNG ou PDF"
        )
    
    try:
        # Ler arquivo
        conteudo = await arquivo.read()
        
        # Converter PDF para imagem se necessário
        if arquivo.content_type == 'application/pdf':
            from pdf2image import convert_from_bytes
            imagens = convert_from_bytes(conteudo)
            if not imagens:
                raise HTTPException(status_code=400, detail="Não foi possível processar o PDF")
            imagem = imagens[0]  # Primeira página
        else:
            imagem = Image.open(io.BytesIO(conteudo))
        
        # Converter para RGB se necessário
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')
        
        # Melhorar qualidade da imagem para OCR
        # Aumentar contraste e tamanho
        from PIL import ImageEnhance, ImageFilter
        
        # Redimensionar se muito pequena
        largura, altura = imagem.size
        if largura < 1000:
            ratio = 1000 / largura
            imagem = imagem.resize((int(largura * ratio), int(altura * ratio)), Image.Resampling.LANCZOS)
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(imagem)
        imagem = enhancer.enhance(1.5)
        
        # Aplicar nitidez
        imagem = imagem.filter(ImageFilter.SHARPEN)
        
        # Executar OCR com configuração para português
        config = '--oem 3 --psm 6 -l por'
        texto = pytesseract.image_to_string(imagem, config=config)
        
        # Detectar tipo de documento
        tipo_documento = detectar_tipo_documento(texto)
        
        # Extrair dados
        dados = {
            "tipo_documento": tipo_documento,
            "texto_bruto": texto[:500],  # Primeiros 500 chars para debug
            "nome": extrair_nome(texto),
            "cpf": extrair_cpf(texto),
            "rg": extrair_rg(texto),
            "rg_orgao_emissor": extrair_orgao_emissor(texto),
            "rg_uf": extrair_uf(texto),
            "data_nascimento": extrair_data_nascimento(texto),
            "nome_pai": extrair_nome_pai(texto),
            "nome_mae": extrair_nome_mae(texto),
            "naturalidade": extrair_naturalidade(texto),
            "naturalidade_uf": extrair_uf(texto),
            "campos_extraidos": 0,
            "confianca": "baixa"
        }
        
        # Contar campos extraídos
        campos = ['nome', 'cpf', 'rg', 'data_nascimento', 'nome_pai', 'nome_mae', 'naturalidade']
        dados["campos_extraidos"] = sum(1 for c in campos if dados.get(c))
        
        # Calcular confiança
        if dados["campos_extraidos"] >= 5:
            dados["confianca"] = "alta"
        elif dados["campos_extraidos"] >= 3:
            dados["confianca"] = "media"
        else:
            dados["confianca"] = "baixa"
        
        return {
            "sucesso": True,
            "mensagem": f"Documento {tipo_documento} processado. {dados['campos_extraidos']} campos extraídos.",
            "dados": dados
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documento: {str(e)}"
        )
