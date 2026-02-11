"""Router de OCR - Extração de dados de documentos"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Optional
from datetime import datetime
import logging

from src.domain.entities import Usuario
from .dependencies import get_current_user
from src.services.ocr_service import OCRService, DocumentParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# Singleton do OCR Service
ocr_service = OCRService()


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
    🚀 Extrai dados de documentos brasileiros (CNH, RG) usando OCR inteligente.
    
    **Features:**
    - 📷 Suporta: JPG, PNG, PDF
    - 🤖 Múltiplos engines: EasyOCR (padrão), Tesseract (fallback)
    - 🇧🇷 Otimizado para documentos brasileiros
    - ⚡ Processamento offline (sem necessidade de API externa)
    
    **Tamanho máximo:** 10MB
    """
    # Validar tipo de arquivo
    tipos_aceitos = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    if arquivo.content_type not in tipos_aceitos:
        raise HTTPException(
            status_code=400,
            detail=f"❌ Tipo de arquivo não suportado. Use: JPG, PNG ou PDF"
        )
    
    try:
        inicio = datetime.now()
        
        # Ler arquivo
        conteudo = await arquivo.read()
        
        # Validar tamanho (10MB máximo)
        tamanho_mb = len(conteudo) / (1024 * 1024)
        if tamanho_mb > 10:
            raise HTTPException(
                status_code=400,
                detail=f"❌ Arquivo muito grande ({tamanho_mb:.1f}MB). Máximo: 10MB"
            )
        
        logger.info(f"Processando arquivo: {arquivo.filename} ({tamanho_mb:.2f}MB)")
        
        # Converter PDF para imagem se necessário
        if arquivo.content_type == 'application/pdf':
            try:
                from pdf2image import convert_from_bytes
                imagens = convert_from_bytes(conteudo)
                if not imagens:
                    raise HTTPException(
                        status_code=400,
                        detail="❌ Não foi possível processar o PDF"
                    )
                # Converter primeira página para bytes
                from PIL import Image
                import io
                img_byte_arr = io.BytesIO()
                imagens[0].save(img_byte_arr, format='PNG')
                conteudo = img_byte_arr.getvalue()
            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="❌ Suporte a PDF não disponível. Use imagens JPG ou PNG."
                )
        
        # Extrair texto usando OCR Service
        texto, confianca_ocr, engine_usado = ocr_service.extrair_texto(conteudo)
        
        # Detectar tipo de documento
        tipo_documento = DocumentParser.detectar_tipo_documento(texto)
        
        # Parsear dados estruturados
        dados = DocumentParser.parsear_documento(texto, tipo_documento)
        
        # Adicionar metadados
        tempo_processamento = (datetime.now() - inicio).total_seconds()
        dados.update({
            "texto_bruto": texto[:500] if len(texto) > 500 else texto,
            "confianca_ocr": round(confianca_ocr, 2),
            "engine_usado": engine_usado,
            "tempo_processamento_segundos": round(tempo_processamento, 2),
            "tamanho_arquivo_mb": round(tamanho_mb, 2)
        })
        
        logger.info(
            f"✅ Documento processado: {tipo_documento}, "
            f"{dados['campos_extraidos']} campos, "
            f"confiança: {dados['confianca']}, "
            f"tempo: {tempo_processamento:.2f}s"
        )
        
        return {
            "sucesso": True,
            "mensagem": (
                f"✅ Documento {tipo_documento} processado com sucesso! "
                f"{dados['campos_extraidos']} campos extraídos "
                f"(confiança: {dados['confianca']})"
            ),
            "dados": dados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar documento: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erro ao processar documento: {str(e)}"
        )
