"""
Serviço de OCR com suporte a múltiplos engines
- EasyOCR (padrão - offline, gratuito)
- Tesseract (fallback - offline, leve)
- Google Cloud Vision (opcional - melhor precisão)
"""
import os
import re
import logging
from typing import Optional, Dict, Tuple, List
from PIL import Image, ImageEnhance, ImageFilter
import io

logger = logging.getLogger(__name__)


class OCRService:
    """Serviço unificado de OCR com múltiplos engines"""
    
    def __init__(self):
        self.engine = os.getenv('OCR_ENGINE', 'easyocr')
        self.languages = os.getenv('OCR_LANGUAGES', 'pt,en').split(',')
        self._easyocr_reader = None
        self._google_vision_client = None
        
        logger.info(f"OCRService iniciado com engine: {self.engine}")
    
    def _get_easyocr_reader(self):
        """Lazy loading do EasyOCR reader"""
        if self._easyocr_reader is None:
            try:
                import easyocr
                logger.info("Inicializando EasyOCR (pode demorar na primeira vez)...")
                self._easyocr_reader = easyocr.Reader(self.languages, gpu=False)
                logger.info("EasyOCR inicializado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao inicializar EasyOCR: {e}")
                raise
        return self._easyocr_reader
    
    def _get_google_vision_client(self):
        """Lazy loading do Google Cloud Vision client"""
        if self._google_vision_client is None:
            try:
                from google.cloud import vision
                credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if not credentials_path:
                    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS não configurado")
                self._google_vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision inicializado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao inicializar Google Vision: {e}")
                raise
        return self._google_vision_client
    
    def preprocessar_imagem(self, imagem: Image.Image) -> Image.Image:
        """Pré-processa imagem para melhorar OCR"""
        # Converter para RGB se necessário
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')
        
        # Redimensionar se muito pequena
        largura, altura = imagem.size
        if largura < 1000:
            ratio = 1000 / largura
            nova_largura = int(largura * ratio)
            nova_altura = int(altura * ratio)
            imagem = imagem.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
            logger.info(f"Imagem redimensionada para {nova_largura}x{nova_altura}")
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(imagem)
        imagem = enhancer.enhance(1.5)
        
        # Aplicar nitidez
        imagem = imagem.filter(ImageFilter.SHARPEN)
        
        return imagem
    
    def extrair_texto_easyocr(self, imagem: Image.Image) -> Tuple[str, float]:
        """Extrai texto usando EasyOCR"""
        try:
            reader = self._get_easyocr_reader()
            
            # Converter PIL Image para bytes
            img_byte_arr = io.BytesIO()
            imagem.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Executar OCR
            results = reader.readtext(img_byte_arr.read(), paragraph=True)
            
            # Combinar todo o texto
            texto_completo = []
            confiancas = []
            
            for detection in results:
                bbox, text, confidence = detection
                texto_completo.append(text)
                confiancas.append(confidence)
            
            texto = '\n'.join(texto_completo)
            confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0.0
            
            logger.info(f"EasyOCR: {len(texto)} caracteres extraídos, confiança: {confianca_media:.2f}")
            return texto, confianca_media
            
        except Exception as e:
            logger.error(f"Erro no EasyOCR: {e}")
            raise
    
    def extrair_texto_tesseract(self, imagem: Image.Image) -> Tuple[str, float]:
        """Extrai texto usando Tesseract"""
        try:
            import pytesseract
            
            # Configuração para português
            config = '--oem 3 --psm 6 -l por'
            texto = pytesseract.image_to_string(imagem, config=config)
            
            # Tesseract não retorna confiança facilmente, estimamos baseado no conteúdo
            confianca = 0.7 if len(texto.strip()) > 50 else 0.5
            
            logger.info(f"Tesseract: {len(texto)} caracteres extraídos")
            return texto, confianca
            
        except Exception as e:
            logger.error(f"Erro no Tesseract: {e}")
            raise
    
    def extrair_texto_google_vision(self, imagem: Image.Image) -> Tuple[str, float]:
        """Extrai texto usando Google Cloud Vision"""
        try:
            from google.cloud import vision
            
            client = self._get_google_vision_client()
            
            # Converter PIL Image para bytes
            img_byte_arr = io.BytesIO()
            imagem.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()
            
            # Criar request
            image = vision.Image(content=content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Extrair texto completo
            texto = response.full_text_annotation.text if response.full_text_annotation else ""
            
            # Calcular confiança baseado em número de palavras detectadas
            num_palavras = len(texto.split())
            confianca = min(num_palavras / 50, 1.0) if num_palavras > 0 else 0.0
            
            logger.info(f"Google Vision: {len(texto)} caracteres extraídos, confiança: {confianca:.2f}")
            return texto, confianca
            
        except Exception as e:
            logger.error(f"Erro no Google Vision: {e}")
            raise
    
    def extrair_texto(self, imagem_bytes: bytes) -> Tuple[str, float, str]:
        """
        Extrai texto da imagem usando o engine configurado
        Retorna: (texto, confianca, engine_usado)
        """
        # Abrir imagem
        imagem = Image.open(io.BytesIO(imagem_bytes))
        
        # Pré-processar
        imagem = self.preprocessar_imagem(imagem)
        
        # Tentar o engine principal
        engine_usado = self.engine
        
        try:
            if self.engine == 'easyocr':
                texto, confianca = self.extrair_texto_easyocr(imagem)
                
            elif self.engine == 'tesseract':
                texto, confianca = self.extrair_texto_tesseract(imagem)
                
            elif self.engine == 'google_vision':
                texto, confianca = self.extrair_texto_google_vision(imagem)
                
            else:
                raise ValueError(f"Engine OCR desconhecido: {self.engine}")
            
            # Se a confiança for muito baixa, tentar fallback
            if confianca < 0.3 and self.engine != 'tesseract':
                logger.warning(f"Confiança baixa ({confianca:.2f}), tentando Tesseract como fallback")
                try:
                    texto_fallback, confianca_fallback = self.extrair_texto_tesseract(imagem)
                    if confianca_fallback > confianca:
                        texto, confianca = texto_fallback, confianca_fallback
                        engine_usado = 'tesseract (fallback)'
                except Exception as e:
                    logger.error(f"Fallback para Tesseract falhou: {e}")
            
            return texto, confianca, engine_usado
            
        except Exception as e:
            # Último recurso: tentar Tesseract
            if self.engine != 'tesseract':
                logger.error(f"Engine {self.engine} falhou, tentando Tesseract: {e}")
                try:
                    texto, confianca = self.extrair_texto_tesseract(imagem)
                    return texto, confianca, 'tesseract (fallback de erro)'
                except Exception as e2:
                    logger.error(f"Todos os engines falharam: {e2}")
                    raise Exception(f"Falha ao processar imagem com qualquer engine OCR")
            else:
                raise


class DocumentParser:
    """Parser de documentos brasileiros (CNH, RG, etc)"""
    
    @staticmethod
    def detectar_tipo_documento(texto: str) -> str:
        """Detecta tipo de documento"""
        texto_upper = texto.upper()
        
        if any(keyword in texto_upper for keyword in ['CARTEIRA NACIONAL', 'CNH', 'HABILITAÇÃO', 'HABILITACAO']):
            return 'CNH'
        elif any(keyword in texto_upper for keyword in ['IDENTIDADE', 'REGISTRO GERAL', 'R.G', 'R G']):
            return 'RG'
        elif any(keyword in texto_upper for keyword in ['CERTIDÃO', 'CERTIDAO', 'NASCIMENTO']):
            return 'CERTIDAO_NASCIMENTO'
        
        return 'DESCONHECIDO'
    
    @staticmethod
    def extrair_cpf(texto: str) -> Optional[str]:
        """Extrai CPF formatado"""
        padrao = r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}'
        match = re.search(padrao, texto)
        if match:
            cpf = re.sub(r'\D', '', match.group())
            if len(cpf) == 11:
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return None
    
    @staticmethod
    def extrair_rg(texto: str) -> Optional[str]:
        """Extrai número de RG"""
        padroes = [
            r'\d{2}\.?\d{3}\.?\d{3}-?\d',
            r'\d{1,2}\.?\d{3}\.?\d{3}',
        ]
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                return match.group()
        return None
    
    @staticmethod
    def extrair_data(texto: str, contexto: Optional[str] = None) -> Optional[str]:
        """Extrai data no formato YYYY-MM-DD"""
        padroes = [
            r'(\d{2}[/\-]\d{2}[/\-]\d{4})',
        ]
        
        if contexto:
            padroes.insert(0, rf'{contexto}[:\s]*(\d{{2}}[/\-]\d{{2}}[/\-]\d{{4}})')
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                data_str = match.group(1) if match.lastindex else match.group()
                data_str = data_str.replace('/', '-')
                partes = data_str.split('-')
                if len(partes) == 3 and len(partes[2]) == 4:
                    return f"{partes[2]}-{partes[1]}-{partes[0]}"
        return None
    
    @staticmethod
    def extrair_nome(texto: str) -> Optional[str]:
        """Extrai nome completo"""
        linhas = texto.split('\n')
        
        for linha in linhas:
            linha_upper = linha.upper().strip()
            
            # Linha com "NOME:"
            if 'NOME' in linha_upper and ':' in linha:
                nome = linha.split(':')[-1].strip()
                if len(nome) > 5 and nome.replace(' ', '').isalpha():
                    return nome.title()
            
            # Linha que parece nome (3+ palavras)
            palavras = linha.strip().split()
            if len(palavras) >= 3:
                eh_nome = all(p.isalpha() or p.upper() in ['DA', 'DE', 'DO', 'DAS', 'DOS'] for p in palavras)
                if eh_nome and len(linha.strip()) > 10:
                    return linha.strip().title()
        
        return None
    
    @staticmethod
    def extrair_nome_mae(texto: str) -> Optional[str]:
        """Extrai nome da mãe"""
        padroes = [
            r'M[AÃ]E[:\s]+([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+)',
            r'FILIA[CÇ][AÃ]O.*?\n([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+)',
        ]
        for padrao in padroes:
            match = re.search(padrao, texto.upper())
            if match:
                nome = match.group(1).strip()
                nome = re.sub(r'\s+', ' ', nome)
                if 5 < len(nome) < 100:
                    return nome.title()
        return None
    
    @staticmethod
    def extrair_orgao_emissor(texto: str) -> Optional[str]:
        """Extrai órgão emissor"""
        orgaos = ['SSP', 'DETRAN', 'PC', 'IFP', 'SESP', 'SDS', 'SEJUSP', 'POLITEC', 'IIRGD']
        texto_upper = texto.upper()
        
        for orgao in orgaos:
            if orgao in texto_upper:
                return orgao
        return None
    
    @staticmethod
    def extrair_uf(texto: str) -> Optional[str]:
        """Extrai UF"""
        ufs = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
               'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
               'SP', 'SE', 'TO']
        
        for uf in ufs:
            if re.search(rf'\b{uf}\b', texto.upper()):
                return uf
        return None
    
    @staticmethod
    def parsear_documento(texto: str, tipo_documento: str) -> Dict:
        """Parseia documento e extrai campos estruturados"""
        dados = {
            "tipo_documento": tipo_documento,
            "nome": DocumentParser.extrair_nome(texto),
            "cpf": DocumentParser.extrair_cpf(texto),
            "data_nascimento": DocumentParser.extrair_data(texto, 'NASCIMENTO'),
            "nome_mae": DocumentParser.extrair_nome_mae(texto),
        }
        
        if tipo_documento == 'RG':
            dados.update({
                "rg": DocumentParser.extrair_rg(texto),
                "rg_orgao_emissor": DocumentParser.extrair_orgao_emissor(texto),
                "rg_uf": DocumentParser.extrair_uf(texto),
            })
        
        # Contar campos preenchidos
        campos_preenchidos = sum(1 for v in dados.values() if v and v != tipo_documento)
        dados['campos_extraidos'] = campos_preenchidos
        
        # Definir confiança
        if campos_preenchidos >= 5:
            dados['confianca'] = 'alta'
        elif campos_preenchidos >= 3:
            dados['confianca'] = 'media'
        else:
            dados['confianca'] = 'baixa'
        
        return dados
