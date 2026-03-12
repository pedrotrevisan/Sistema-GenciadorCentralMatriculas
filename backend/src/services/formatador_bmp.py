"""
Serviço de Formatação de Planilhas BMP (Brasil Mais Produtivo)
Padronização avançada para dados de matrícula do SENAI

Funcionalidades:
- Conversão de nomes CAIXA ALTA para Title Case com acentuação
- Validação de CPF com dígitos verificadores
- Formatação de CEP (00.000-000)
- Formatação de telefones (apenas números, 10-11 dígitos)
- Padronização de e-mails (minúsculas)
- Padronização de endereços
- Correção ortográfica de nomes próprios brasileiros
- Relatório de auditoria detalhado
- Exportação para Template TOTVS
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


# Dicionário EXPANDIDO de correções ortográficas para nomes brasileiros
CORRECOES_NOMES = {
    # Nomes com acento agudo
    'JOAO': 'João', 'JOSE': 'José', 'MARIA': 'Maria',
    'VALERIA': 'Valéria', 'DEBORA': 'Débora', 'BARBARA': 'Bárbara',
    'MARCIA': 'Márcia', 'LUCIA': 'Lúcia', 'LUCIO': 'Lúcio',
    'MARCIO': 'Márcio', 'SERGIO': 'Sérgio', 'ROGERIO': 'Rogério',
    'ANDRE': 'André', 'CANDIDO': 'Cândido', 'CLAUDIO': 'Cláudio',
    'FABIO': 'Fábio', 'FLAVIO': 'Flávio', 'JULIO': 'Júlio',
    'MAURICIO': 'Maurício', 'OTAVIO': 'Otávio', 'ANTONIO': 'Antônio',
    'THIAGO': 'Thiago', 'MATHEUS': 'Matheus', 'LUCAS': 'Lucas',
    'GABRIEL': 'Gabriel', 'RAFAEL': 'Rafael', 'DANIEL': 'Daniel',
    'CICERO': 'Cícero', 'JERONIMO': 'Jerônimo', 'RAMIRO': 'Ramiro',
    'LUIZ': 'Luiz', 'LUIS': 'Luís', 'RAUL': 'Raul',
    'NATALIA': 'Natália', 'LIVIA': 'Lívia', 'SILVIA': 'Sílvia',
    'CECILIA': 'Cecília', 'EMILIA': 'Emília', 'JULIA': 'Júlia',
    'HELIO': 'Hélio', 'HELOISA': 'Heloísa', 'CLARICE': 'Clarice',
    'BEATRIZ': 'Beatriz', 'PATRICIA': 'Patrícia', 'MONICA': 'Mônica',
    'PRISCILA': 'Priscila', 'LETICIA': 'Letícia', 'SIMONE': 'Simone',
    'BRUNA': 'Bruna', 'BRUNO': 'Bruno', 'CAIO': 'Caio',
    'SOFIA': 'Sofia', 'SOPHIA': 'Sophia', 'ANA': 'Ana',
    'ENZO': 'Enzo', 'HEITOR': 'Heitor', 'PEDRO': 'Pedro',
    'VITOR': 'Vítor', 'VICTOR': 'Victor', 'DAVI': 'Davi',
    'ISAIAS': 'Isaías', 'MATIAS': 'Matias', 'ELIAS': 'Elias',
    'JEREMIAS': 'Jeremias', 'TOBIAS': 'Tobias', 'JONAS': 'Jonas',
    'MOISES': 'Moisés', 'TOMAS': 'Tomás', 'NICOLAS': 'Nicolas',
    'TIAGO': 'Tiago', 'DIEGO': 'Diego', 'DIOGO': 'Diogo',
    
    # Nomes com til
    'CONCEICAO': 'Conceição', 'ENCARNACAO': 'Encarnação',
    'ASSUNCAO': 'Assunção', 'ANUNCIACAO': 'Anunciação',
    'GERMANO': 'Germano', 'ADRIANO': 'Adriano',
    'CRISTIANO': 'Cristiano', 'LUCIANO': 'Luciano',
    'MARIANO': 'Mariano', 'FABIANO': 'Fabiano',
    'SIMAO': 'Simão', 'JOAO': 'João', 'SEBASTIAO': 'Sebastião',
    'CRISTOVAO': 'Cristóvão', 'ADAO': 'Adão', 'FERNAO': 'Fernão',
    'JORDAO': 'Jordão',
    
    # Sobrenomes com cedilha
    'GONCALVES': 'Gonçalves', 'FRANCA': 'França', 'LANCA': 'Lança',
    'ALCANTARA': 'Alcântara', 'FALCAO': 'Falcão',
    
    # Sobrenomes com acento
    'ARAUJO': 'Araújo', 'MERCES': 'Mercês',
    'FRANCES': 'Francês', 'INES': 'Inês', 'AGNES': 'Agnês',
    'SOUZA': 'Souza', 'SOUSA': 'Sousa',
    'MACEDO': 'Macedo', 'PESSOA': 'Pessoa',
    'FREITAS': 'Freitas', 'SANTOS': 'Santos',
    'OLIVEIRA': 'Oliveira', 'SILVA': 'Silva',
    'PEREIRA': 'Pereira', 'FERREIRA': 'Ferreira',
    'ALMEIDA': 'Almeida', 'RIBEIRO': 'Ribeiro',
    'CARVALHO': 'Carvalho', 'MENDES': 'Mendes',
    'NUNES': 'Nunes', 'MARTINS': 'Martins',
    'RODRIGUES': 'Rodrigues', 'BARBOSA': 'Barbosa',
    'COSTA': 'Costa', 'GOMES': 'Gomes',
    'LIMA': 'Lima', 'LOPES': 'Lopes',
    'MOREIRA': 'Moreira', 'TEIXEIRA': 'Teixeira',
    'REIS': 'Reis', 'DIAS': 'Dias', 'VIEIRA': 'Vieira',
    'MONTEIRO': 'Monteiro', 'ANDRADE': 'Andrade',
    'NASCIMENTO': 'Nascimento', 'SOARES': 'Soares',
    'MELO': 'Melo', 'AZEVEDO': 'Azevedo',
    'BORGES': 'Borges', 'BATISTA': 'Batista',
    'SANTANA': 'Santana', 'BISPO': 'Bispo',
    'ASSIS': 'Assis', 'JESUS': 'Jesus',
    
    # Estados brasileiros (para naturalidade)
    'BAHIA': 'Bahia', 'SAO PAULO': 'São Paulo',
    'RIO DE JANEIRO': 'Rio de Janeiro', 'MINAS GERAIS': 'Minas Gerais',
    'PERNAMBUCO': 'Pernambuco', 'CEARA': 'Ceará',
    'PARA': 'Pará', 'MARANHAO': 'Maranhão',
    'GOIAS': 'Goiás', 'PARANA': 'Paraná',
    'PIAUI': 'Piauí', 'AMAPA': 'Amapá',
    'RONDONIA': 'Rondônia', 'ESPIRITO SANTO': 'Espírito Santo',
    
    # Cidades comuns da Bahia
    'SALVADOR': 'Salvador', 'FEIRA DE SANTANA': 'Feira de Santana',
    'SIMOES FILHO': 'Simões Filho', 'CAMACARI': 'Camaçari',
    'LAURO DE FREITAS': 'Lauro de Freitas', 'CANDEIAS': 'Candeias',
    'ITABUNA': 'Itabuna', 'VITORIA DA CONQUISTA': 'Vitória da Conquista',
    'ILHEUS': 'Ilhéus', 'JUAZEIRO': 'Juazeiro',
}

# Preposições que devem ficar em minúsculo
PREPOSICOES = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'a', 'o', 'ao', 'aos', 
               'para', 'por', 'com', 'sem', 'num', 'numa', 'du', 'di'}


@dataclass
class AuditoriaFormatacao:
    """Resultado da auditoria de formatação"""
    total_linhas: int = 0
    nomes_padronizados: int = 0
    enderecos_padronizados: int = 0
    correcoes_ortograficas: int = 0
    acentos_corrigidos: int = 0
    cpfs_validos: int = 0
    cpfs_invalidos: int = 0
    ceps_formatados: int = 0
    telefones_formatados: int = 0
    emails_ajustados: int = 0
    pendencias_validacao: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'total_linhas': self.total_linhas,
            'nomes_padronizados': self.nomes_padronizados,
            'enderecos_padronizados': self.enderecos_padronizados,
            'correcoes_ortograficas': self.correcoes_ortograficas,
            'acentos_corrigidos': self.acentos_corrigidos,
            'cpfs_validos': self.cpfs_validos,
            'cpfs_invalidos': self.cpfs_invalidos,
            'ceps_formatados': self.ceps_formatados,
            'telefones_formatados': self.telefones_formatados,
            'emails_ajustados': self.emails_ajustados,
            'pendencias_validacao': self.pendencias_validacao
        }


class FormatadorBMP:
    """Formatador avançado para planilhas BMP"""
    
    def __init__(self):
        self.auditoria = AuditoriaFormatacao()
    
    def _remover_acentos(self, texto: str) -> str:
        """Remove acentos para comparação"""
        nfkd = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))
    
    def _corrigir_palavra(self, palavra: str) -> Tuple[str, bool]:
        """
        Corrige uma palavra aplicando acentuação correta
        Retorna: (palavra_corrigida, foi_corrigida)
        """
        palavra_upper = palavra.upper()
        palavra_sem_acento = self._remover_acentos(palavra_upper)
        
        # Verificar no dicionário de correções
        if palavra_sem_acento in CORRECOES_NOMES:
            correcao = CORRECOES_NOMES[palavra_sem_acento]
            if palavra_upper != correcao.upper():
                return correcao, True
            return correcao, False
        
        # Se não está no dicionário, aplicar Title Case básico
        return palavra.capitalize(), False
    
    def formatar_nome(self, nome: str) -> Tuple[str, Dict]:
        """
        Formata nome para Title Case brasileiro com correção ortográfica
        
        Retorna: (nome_formatado, metadados)
        """
        if not nome or not isinstance(nome, str):
            return nome, {'modificado': False}
        
        nome = nome.strip()
        if not nome:
            return nome, {'modificado': False}
        
        original = nome
        palavras = nome.split()
        resultado = []
        correcoes = 0
        acentos = 0
        
        for i, palavra in enumerate(palavras):
            palavra_lower = palavra.lower()
            
            # Preposições em minúsculo (exceto primeira palavra)
            if palavra_lower in PREPOSICOES and i > 0:
                resultado.append(palavra_lower)
                continue
            
            # Corrigir palavra
            corrigida, foi_corrigida = self._corrigir_palavra(palavra)
            
            if foi_corrigida:
                # Verificar se foi correção de acento
                if self._remover_acentos(palavra.upper()) == self._remover_acentos(corrigida.upper()):
                    acentos += 1
                else:
                    correcoes += 1
            
            resultado.append(corrigida)
        
        nome_formatado = ' '.join(resultado)
        
        return nome_formatado, {
            'modificado': nome_formatado != original,
            'original': original,
            'correcoes_ortograficas': correcoes,
            'acentos_corrigidos': acentos
        }
    
    def formatar_endereco(self, endereco: str) -> Tuple[str, Dict]:
        """
        Formata endereço para Title Case brasileiro
        """
        if not endereco or not isinstance(endereco, str):
            return endereco, {'modificado': False}
        
        endereco = endereco.strip()
        if not endereco:
            return endereco, {'modificado': False}
        
        original = endereco
        
        # Tipos de logradouro
        tipos_logradouro = {
            'RUA': 'Rua', 'AVENIDA': 'Avenida', 'AV': 'Av.',
            'TRAVESSA': 'Travessa', 'TRAV': 'Trav.',
            'ALAMEDA': 'Alameda', 'AL': 'Al.',
            'PRACA': 'Praça', 'PCA': 'Pça.',
            'LARGO': 'Largo', 'BECO': 'Beco',
            'ESTRADA': 'Estrada', 'EST': 'Est.',
            'RODOVIA': 'Rodovia', 'ROD': 'Rod.',
            'LADEIRA': 'Ladeira', 'VILA': 'Vila',
            'QUADRA': 'Quadra', 'QD': 'Qd.',
            'CONJUNTO': 'Conjunto', 'CONJ': 'Conj.',
            'LOTE': 'Lote', 'LT': 'Lt.'
        }
        
        palavras = endereco.split()
        resultado = []
        
        for i, palavra in enumerate(palavras):
            palavra_upper = palavra.upper().rstrip('.,')
            
            # Tipo de logradouro
            if palavra_upper in tipos_logradouro:
                resultado.append(tipos_logradouro[palavra_upper])
                continue
            
            # Preposições
            if palavra.lower() in PREPOSICOES and i > 0:
                resultado.append(palavra.lower())
                continue
            
            # Números
            if palavra.replace('-', '').replace('/', '').isdigit():
                resultado.append(palavra)
                continue
            
            # Aplicar formatação de nome para o restante
            corrigida, _ = self._corrigir_palavra(palavra)
            resultado.append(corrigida)
        
        endereco_formatado = ' '.join(resultado)
        
        return endereco_formatado, {
            'modificado': endereco_formatado != original,
            'original': original
        }
    
    def validar_cpf(self, cpf: str) -> Tuple[str, bool, str]:
        """
        Valida e formata CPF brasileiro
        
        Retorna: (cpf_formatado, is_valido, mensagem)
        """
        if not cpf or not isinstance(cpf, str):
            return '', False, 'CPF vazio'
        
        # Remover formatação
        cpf_numeros = re.sub(r'\D', '', str(cpf))
        
        if not cpf_numeros:
            return '', False, 'CPF vazio'
        
        if len(cpf_numeros) != 11:
            return cpf, False, f'CPF deve ter 11 dígitos (tem {len(cpf_numeros)})'
        
        # Verificar se todos os dígitos são iguais
        if len(set(cpf_numeros)) == 1:
            return cpf, False, 'CPF inválido (dígitos repetidos)'
        
        # Validar dígitos verificadores
        def calcular_digito(cpf_parcial: str, pesos: List[int]) -> int:
            soma = sum(int(d) * p for d, p in zip(cpf_parcial, pesos))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        # Primeiro dígito
        pesos1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        digito1 = calcular_digito(cpf_numeros[:9], pesos1)
        
        if int(cpf_numeros[9]) != digito1:
            return cpf, False, 'CPF inválido (dígito verificador 1)'
        
        # Segundo dígito
        pesos2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        digito2 = calcular_digito(cpf_numeros[:10], pesos2)
        
        if int(cpf_numeros[10]) != digito2:
            return cpf, False, 'CPF inválido (dígito verificador 2)'
        
        # Formatar
        cpf_formatado = f'{cpf_numeros[:3]}.{cpf_numeros[3:6]}.{cpf_numeros[6:9]}-{cpf_numeros[9:]}'
        
        return cpf_formatado, True, 'CPF válido'
    
    def formatar_cep(self, cep: str) -> Tuple[str, bool, str]:
        """
        Formata CEP brasileiro (00.000-000)
        
        Retorna: (cep_formatado, is_valido, mensagem)
        """
        if not cep or not isinstance(cep, str):
            return '', False, 'CEP vazio'
        
        # Remover formatação
        cep_numeros = re.sub(r'\D', '', str(cep))
        
        if not cep_numeros:
            return '', False, 'CEP vazio'
        
        if len(cep_numeros) != 8:
            return cep, False, f'CEP deve ter 8 dígitos (tem {len(cep_numeros)})'
        
        # Formatar como 00.000-000
        cep_formatado = f'{cep_numeros[:2]}.{cep_numeros[2:5]}-{cep_numeros[5:]}'
        
        return cep_formatado, True, 'CEP formatado'
    
    def formatar_telefone(self, telefone: str) -> Tuple[str, bool, str]:
        """
        Formata telefone brasileiro (apenas números)
        
        Retorna: (telefone_formatado, is_valido, mensagem)
        """
        if not telefone or not isinstance(telefone, str):
            return '', False, 'Telefone vazio'
        
        # Remover tudo que não é número
        tel_numeros = re.sub(r'\D', '', str(telefone))
        
        if not tel_numeros:
            return '', False, 'Telefone vazio'
        
        # Verificar tamanho
        if len(tel_numeros) < 10:
            return telefone, False, f'Telefone incompleto ({len(tel_numeros)} dígitos)'
        
        if len(tel_numeros) > 11:
            return telefone, False, f'Telefone muito longo ({len(tel_numeros)} dígitos)'
        
        return tel_numeros, True, 'Telefone formatado'
    
    def formatar_email(self, email: str) -> Tuple[str, bool, str]:
        """
        Formata e-mail (minúsculas, sem espaços)
        
        Retorna: (email_formatado, is_valido, mensagem)
        """
        if not email or not isinstance(email, str):
            return '', False, 'E-mail vazio'
        
        email = email.strip().lower()
        
        if not email:
            return '', False, 'E-mail vazio'
        
        # Validação básica
        if '@' not in email or '.' not in email.split('@')[-1]:
            return email, False, 'E-mail em formato inválido'
        
        return email, True, 'E-mail formatado'
    
    def formatar_data(self, data: str) -> Tuple[str, bool, str]:
        """
        Formata data para DD/MM/AAAA
        
        Retorna: (data_formatada, is_valida, mensagem)
        """
        if not data or not isinstance(data, str):
            return '', False, 'Data vazia'
        
        data = str(data).strip()
        
        if not data:
            return '', False, 'Data vazia'
        
        # Tentar diferentes formatos
        import re
        
        # Formato DD.MM.AAAA ou DD/MM/AAAA ou DD-MM-AAAA
        match = re.match(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', data)
        if match:
            dia, mes, ano = match.groups()
            dia = dia.zfill(2)
            mes = mes.zfill(2)
            if len(ano) == 2:
                ano = '20' + ano if int(ano) < 50 else '19' + ano
            return f'{dia}/{mes}/{ano}', True, 'Data formatada'
        
        return data, False, 'Formato de data não reconhecido'
    
    def processar_registro(self, registro: Dict, mapeamento_colunas: Dict) -> Dict:
        """
        Processa um registro completo aplicando todas as formatações
        """
        resultado = registro.copy()
        erros = []
        avisos = []
        
        # Processar cada tipo de campo
        for campo, valor in registro.items():
            if not valor or (isinstance(valor, float) and str(valor) == 'nan'):
                continue
            
            valor = str(valor).strip()
            tipo = mapeamento_colunas.get(campo, 'texto')
            
            if tipo == 'nome':
                formatado, meta = self.formatar_nome(valor)
                resultado[campo] = formatado
                if meta.get('modificado'):
                    self.auditoria.nomes_padronizados += 1
                if meta.get('correcoes_ortograficas', 0) > 0:
                    self.auditoria.correcoes_ortograficas += meta['correcoes_ortograficas']
                if meta.get('acentos_corrigidos', 0) > 0:
                    self.auditoria.acentos_corrigidos += meta['acentos_corrigidos']
            
            elif tipo == 'endereco':
                formatado, meta = self.formatar_endereco(valor)
                resultado[campo] = formatado
                if meta.get('modificado'):
                    self.auditoria.enderecos_padronizados += 1
            
            elif tipo == 'cpf':
                formatado, valido, msg = self.validar_cpf(valor)
                resultado[campo] = formatado
                if valido:
                    self.auditoria.cpfs_validos += 1
                else:
                    self.auditoria.cpfs_invalidos += 1
                    erros.append(f'CPF: {msg}')
            
            elif tipo == 'cep':
                formatado, valido, msg = self.formatar_cep(valor)
                resultado[campo] = formatado
                if valido:
                    self.auditoria.ceps_formatados += 1
                elif msg != 'CEP vazio':
                    avisos.append(f'CEP: {msg}')
            
            elif tipo == 'telefone':
                formatado, valido, msg = self.formatar_telefone(valor)
                resultado[campo] = formatado
                if valido:
                    self.auditoria.telefones_formatados += 1
                elif msg != 'Telefone vazio':
                    avisos.append(f'Telefone: {msg}')
            
            elif tipo == 'email':
                formatado, valido, msg = self.formatar_email(valor)
                resultado[campo] = formatado
                if valido:
                    self.auditoria.emails_ajustados += 1
                elif msg != 'E-mail vazio':
                    avisos.append(f'E-mail: {msg}')
            
            elif tipo == 'data':
                formatado, valido, msg = self.formatar_data(valor)
                resultado[campo] = formatado
        
        resultado['_ERROS'] = '; '.join(erros) if erros else ''
        resultado['_AVISOS'] = '; '.join(avisos) if avisos else ''
        resultado['_STATUS'] = 'ERRO' if erros else ('AVISO' if avisos else 'OK')
        
        return resultado
    
    def detectar_tipo_coluna(self, nome_coluna: str, valores_amostra: List) -> str:
        """
        Detecta automaticamente o tipo de uma coluna
        """
        nome_lower = nome_coluna.lower()
        
        # Por nome da coluna
        if any(x in nome_lower for x in ['cpf']):
            return 'cpf'
        if any(x in nome_lower for x in ['cep', 'codigo postal']):
            return 'cep'
        if any(x in nome_lower for x in ['email', 'e-mail']):
            return 'email'
        if any(x in nome_lower for x in ['telefone', 'celular', 'fone', 'tel']):
            return 'telefone'
        if any(x in nome_lower for x in ['data', 'nascimento', 'emissao', 'emissão']):
            return 'data'
        if any(x in nome_lower for x in ['endereco', 'endereço', 'logradouro', 'rua', 'av']):
            return 'endereco'
        if any(x in nome_lower for x in ['nome', 'aluno', 'responsavel', 'responsável', 'mae', 'mãe', 'pai']):
            return 'nome'
        if any(x in nome_lower for x in ['bairro', 'cidade', 'municipio', 'município', 'naturalidade']):
            return 'endereco'
        
        return 'texto'
    
    def get_auditoria(self) -> Dict:
        """Retorna relatório de auditoria"""
        return self.auditoria.to_dict()


# Instância global
formatador_bmp = FormatadorBMP()
