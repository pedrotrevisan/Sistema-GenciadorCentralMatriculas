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


@router.get("/info")
async def ocr_info():
    """📋 Informações sobre o sistema OCR"""
    import os
    engine = os.getenv('OCR_ENGINE', 'easyocr')
    
    engines_info = {
        'easyocr': {
            'nome': 'EasyOCR',
            'status': 'offline',
            'precisao': 'alta',
            'velocidade': 'média',
            'suporte': '80+ idiomas incluindo português'
        },
        'tesseract': {
            'nome': 'Tesseract OCR',
            'status': 'offline',
            'precisao': 'média',
            'velocidade': 'rápida',
            'suporte': 'português e outros'
        },
        'google_vision': {
            'nome': 'Google Cloud Vision',
            'status': 'online (requer API key)',
            'precisao': 'muito alta',
            'velocidade': 'rápida',
            'suporte': '200+ idiomas'
        }
    }
    
    return {
        "engine_atual": engine,
        "detalhes": engines_info.get(engine, {}),
        "engines_disponiveis": engines_info,
        "documentos_suportados": ["CNH", "RG", "Certidão de Nascimento"],
        "formatos_aceitos": ["JPG", "PNG", "PDF"],
        "tamanho_maximo_mb": 10
    }


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
