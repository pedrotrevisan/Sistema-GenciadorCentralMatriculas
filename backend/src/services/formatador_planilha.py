"""
Serviço de Formatação e Validação de Planilhas de Matrícula
Corrige e padroniza dados vindos das empresas
"""
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import unicodedata


class FormatadorPlanilha:
    """Formatador de dados de matrícula seguindo regras do SYNAPSE e padrão BMP"""
    
    # Preposições que devem ficar em minúsculo nos nomes
    PREPOSICOES = {'da', 'de', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'a', 'o', 'ao', 'aos'}
    
    # Estados brasileiros
    ESTADOS_BR = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
        'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
        'SP', 'SE', 'TO'
    }
    
    # Dicionário de correções ortográficas para nomes brasileiros
    CORRECOES_NOMES = {
        'JOAO': 'João', 'JOSE': 'José', 'MARIA': 'Maria',
        'CONCEICAO': 'Conceição', 'GONCALVES': 'Gonçalves', 
        'FALCAO': 'Falcão', 'ALCANTARA': 'Alcântara',
        'FRANCES': 'Francês', 'INES': 'Inês', 'AGNES': 'Agnês',
        'VALERIA': 'Valéria', 'DEBORA': 'Débora', 'BARBARA': 'Bárbara',
        'MARCIA': 'Márcia', 'LUCIA': 'Lúcia', 'LUCIO': 'Lúcio',
        'MARCIO': 'Márcio', 'SERGIO': 'Sérgio', 'ROGERIO': 'Rogério',
        'ANDRE': 'André', 'CANDIDO': 'Cândido', 'CLAUDIO': 'Cláudio',
        'FABIO': 'Fábio', 'FLAVIO': 'Flávio', 'JULIO': 'Júlio',
        'MAURICIO': 'Maurício', 'OTAVIO': 'Otávio', 'ANTONIO': 'Antônio',
        'THIAGO': 'Thiago', 'MATHEUS': 'Matheus', 'LUCAS': 'Lucas',
        'GABRIEL': 'Gabriel', 'RAFAEL': 'Rafael', 'DANIEL': 'Daniel',
        'FERNAO': 'Fernão', 'SIMAO': 'Simão', 'JORDAO': 'Jordão',
        'ADAO': 'Adão', 'CRISTOVAO': 'Cristóvão', 'SEBASTIAO': 'Sebastião',
        'CICERO': 'Cícero', 'JERONIMO': 'Jerônimo',
        'ARAUJO': 'Araújo', 'FRANCA': 'França', 
        'ASSUNCAO': 'Assunção', 'ENCARNACAO': 'Encarnação',
        'MERCES': 'Mercês', 'LANCA': 'Lança',
    }

    @staticmethod
    def _remover_acentos(texto: str) -> str:
        """Remove acentos para comparação"""
        nfkd = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    @staticmethod
    def formatar_nome(nome: str) -> Tuple[str, bool, str]:
        """
        Formata nome próprio seguindo regras brasileiras com correção ortográfica
        Retorna: (nome_formatado, is_valido, mensagem_erro)
        
        Regras:
        - Primeira letra de cada palavra em maiúscula
        - Preposições (da, de, do, etc.) em minúscula
        - Correção de acentuação (JOAO → João, FALCAO → Falcão)
        - Remove espaços extras
        """
        if not nome or not isinstance(nome, str):
            return "", False, "Nome vazio ou inválido"
        
        # Limpar espaços extras
        nome = ' '.join(nome.strip().split())
        
        if len(nome) < 3:
            return nome, False, "Nome muito curto"
        
        # Verificar se tem pelo menos 2 palavras (nome e sobrenome)
        palavras = nome.split()
        if len(palavras) < 2:
            return nome.title(), False, "Nome incompleto (falta sobrenome)"
        
        # Formatar cada palavra com correção ortográfica
        palavras_formatadas = []
        for i, palavra in enumerate(palavras):
            palavra_lower = palavra.lower()
            palavra_upper = palavra.upper()
            palavra_sem_acento = FormatadorPlanilha._remover_acentos(palavra_upper)
            
            # Preposições ficam em minúscula (exceto se for a primeira palavra)
            if i > 0 and palavra_lower in FormatadorPlanilha.PREPOSICOES:
                palavras_formatadas.append(palavra_lower)
            # Verificar se tem correção ortográfica
            elif palavra_sem_acento in FormatadorPlanilha.CORRECOES_NOMES:
                palavras_formatadas.append(FormatadorPlanilha.CORRECOES_NOMES[palavra_sem_acento])
            else:
                # Primeira letra maiúscula, resto minúscula
                palavras_formatadas.append(palavra.capitalize())
        
        nome_formatado = ' '.join(palavras_formatadas)
        return nome_formatado, True, ""

    @staticmethod
    def validar_cpf(cpf: str) -> Tuple[bool, str]:
        """
        Valida CPF usando algoritmo oficial dos dígitos verificadores
        Retorna: (is_valido, mensagem)
        """
        # Remove caracteres não numéricos
        cpf_limpo = re.sub(r'\D', '', str(cpf))
        
        if len(cpf_limpo) != 11:
            return False, f"CPF deve ter 11 dígitos (tem {len(cpf_limpo)})"
        
        # Verifica se todos os dígitos são iguais
        if cpf_limpo == cpf_limpo[0] * 11:
            return False, "CPF inválido (dígitos repetidos)"
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf_limpo[9]):
            return False, "CPF inválido (dígito verificador incorreto)"
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf_limpo[10]):
            return False, "CPF inválido (dígito verificador incorreto)"
        
        return True, "CPF válido"

    @staticmethod
    def formatar_cpf(cpf: str) -> Tuple[str, bool, str]:
        """
        Formata CPF para padrão 000.000.000-00
        Retorna: (cpf_formatado, is_valido, mensagem)
        """
        cpf_limpo = re.sub(r'\D', '', str(cpf))
        
        if len(cpf_limpo) != 11:
            return cpf, False, f"CPF deve ter 11 dígitos (tem {len(cpf_limpo)})"
        
        # Valida
        is_valido, msg = FormatadorPlanilha.validar_cpf(cpf_limpo)
        
        # Formata
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        
        return cpf_formatado, is_valido, msg

    @staticmethod
    def formatar_telefone(telefone: str) -> Tuple[str, bool, str]:
        """
        Formata telefone para padrão APENAS NÚMEROS (sem máscara)
        Exemplo: 7199886664
        Retorna: (telefone_formatado, is_valido, mensagem)
        """
        if not telefone:
            return "", False, "Telefone vazio"
        
        # Remove tudo que não é dígito
        tel_limpo = re.sub(r'\D', '', str(telefone))
        
        # Adiciona DDD 71 se não tiver (padrão Bahia)
        if len(tel_limpo) == 8:
            tel_limpo = '71' + tel_limpo
        elif len(tel_limpo) == 9:
            tel_limpo = '71' + tel_limpo
        
        if len(tel_limpo) == 10 or len(tel_limpo) == 11:
            # Retorna apenas os números, sem máscara
            return tel_limpo, True, ""
        else:
            return telefone, False, f"Telefone inválido ({len(tel_limpo)} dígitos)"

    @staticmethod
    def formatar_email(email: str) -> Tuple[str, bool, str]:
        """
        Valida e formata email (lowercase)
        Retorna: (email_formatado, is_valido, mensagem)
        """
        if not email or not isinstance(email, str):
            return "", False, "Email vazio"
        
        # Se tiver múltiplos emails, pegar o primeiro
        email = email.strip().split('\n')[0].strip()
        email = email.lower()
        
        # Validação básica
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return email, True, ""
        else:
            return email, False, "Email em formato inválido"

    @staticmethod
    def formatar_cep(cep: str) -> Tuple[str, bool, str]:
        """
        Formata CEP para padrão 00000-000
        Retorna: (cep_formatado, is_valido, mensagem)
        """
        if not cep:
            return "", False, "CEP vazio"
        
        cep_limpo = re.sub(r'\D', '', str(cep))
        
        if len(cep_limpo) != 8:
            return cep, False, f"CEP deve ter 8 dígitos (tem {len(cep_limpo)})"
        
        cep_formatado = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        return cep_formatado, True, ""

    @staticmethod
    def formatar_data(data) -> Tuple[str, bool, str]:
        """
        Formata data para padrão DD/MM/AAAA
        Aceita: datetime, string em vários formatos
        """
        if data is None:
            return "", False, "Data vazia"
        
        # Se já é datetime
        if isinstance(data, datetime):
            return data.strftime("%d/%m/%Y"), True, ""
        
        data_str = str(data).strip()
        
        # Tenta vários formatos
        formatos = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
        ]
        
        for fmt in formatos:
            try:
                dt = datetime.strptime(data_str.split()[0], fmt.split()[0])
                return dt.strftime("%d/%m/%Y"), True, ""
            except:
                continue
        
        return data_str, False, "Formato de data não reconhecido"

    @staticmethod
    def formatar_rg(rg: str) -> str:
        """Remove formatação do RG, mantém só números"""
        if not rg:
            return ""
        return re.sub(r'\D', '', str(rg))

    @staticmethod
    def formatar_funcao(funcao: str) -> str:
        """Formata função/cargo"""
        if not funcao:
            return ""
        # Title case mas mantém siglas
        return ' '.join(funcao.strip().split()).title()


def processar_linha_aluno(dados: Dict) -> Dict:
    """
    Processa uma linha de dados de aluno e retorna formatado
    
    Entrada esperada:
    {
        'nome': str,
        'email': str,
        'cpf': str,
        'telefone': str,
        'funcao': str,
        'rg': str,
        'data_emissao_rg': str/datetime,
        'orgao_emissor': str,
        'naturalidade': str,
        'data_nascimento': str/datetime,
        'nome_pai': str,
        'nome_mae': str,
        'endereco': str,
        'numero': str,
        'bairro': str,
        'cep': str,
        # Campos do responsável (se menor)
        'resp_nome': str,
        'resp_rg': str,
        'resp_data_rg': str/datetime,
        'resp_cpf': str,
        'resp_nascimento': str/datetime,
    }
    """
    f = FormatadorPlanilha
    erros = []
    avisos = []
    
    resultado = {
        'original': dados.copy(),
        'formatado': {},
        'erros': [],
        'avisos': [],
        'status': 'OK'
    }
    
    # Nome
    nome_fmt, nome_ok, nome_msg = f.formatar_nome(dados.get('nome', ''))
    resultado['formatado']['nome'] = nome_fmt
    if not nome_ok:
        erros.append(f"Nome: {nome_msg}")
    
    # Email
    email_fmt, email_ok, email_msg = f.formatar_email(dados.get('email', ''))
    resultado['formatado']['email'] = email_fmt
    if not email_ok:
        avisos.append(f"Email: {email_msg}")
    
    # CPF
    cpf_fmt, cpf_ok, cpf_msg = f.formatar_cpf(dados.get('cpf', ''))
    resultado['formatado']['cpf'] = cpf_fmt
    if not cpf_ok:
        erros.append(f"CPF: {cpf_msg}")
    
    # Telefone
    tel_fmt, tel_ok, tel_msg = f.formatar_telefone(dados.get('telefone', ''))
    resultado['formatado']['telefone'] = tel_fmt
    if not tel_ok:
        avisos.append(f"Telefone: {tel_msg}")
    
    # Função
    resultado['formatado']['funcao'] = f.formatar_funcao(dados.get('funcao', ''))
    
    # RG
    resultado['formatado']['rg'] = f.formatar_rg(dados.get('rg', ''))
    
    # Data emissão RG
    data_rg_fmt, _, _ = f.formatar_data(dados.get('data_emissao_rg'))
    resultado['formatado']['data_emissao_rg'] = data_rg_fmt
    
    # Órgão emissor (uppercase)
    orgao = str(dados.get('orgao_emissor', '')).strip().upper()
    resultado['formatado']['orgao_emissor'] = orgao
    
    # Naturalidade
    nat_fmt, _, _ = f.formatar_nome(dados.get('naturalidade', ''))
    resultado['formatado']['naturalidade'] = nat_fmt
    
    # Data nascimento
    nasc_fmt, nasc_ok, nasc_msg = f.formatar_data(dados.get('data_nascimento'))
    resultado['formatado']['data_nascimento'] = nasc_fmt
    if not nasc_ok and dados.get('data_nascimento'):
        avisos.append(f"Data nascimento: {nasc_msg}")
    
    # Nomes dos pais
    pai_fmt, _, _ = f.formatar_nome(dados.get('nome_pai', ''))
    resultado['formatado']['nome_pai'] = pai_fmt
    
    mae_fmt, _, _ = f.formatar_nome(dados.get('nome_mae', ''))
    resultado['formatado']['nome_mae'] = mae_fmt
    
    # Endereço
    resultado['formatado']['endereco'] = ' '.join(str(dados.get('endereco', '')).strip().split()).title()
    resultado['formatado']['numero'] = str(dados.get('numero', '')).strip()
    resultado['formatado']['bairro'] = ' '.join(str(dados.get('bairro', '')).strip().split()).title()
    
    # CEP
    cep_fmt, cep_ok, cep_msg = f.formatar_cep(dados.get('cep', ''))
    resultado['formatado']['cep'] = cep_fmt
    if not cep_ok and dados.get('cep'):
        avisos.append(f"CEP: {cep_msg}")
    
    # Campos do responsável (se existirem)
    if dados.get('resp_nome'):
        resp_nome_fmt, _, _ = f.formatar_nome(dados.get('resp_nome', ''))
        resultado['formatado']['resp_nome'] = resp_nome_fmt
        
        resp_cpf_fmt, resp_cpf_ok, resp_cpf_msg = f.formatar_cpf(dados.get('resp_cpf', ''))
        resultado['formatado']['resp_cpf'] = resp_cpf_fmt
        if not resp_cpf_ok and dados.get('resp_cpf'):
            erros.append(f"CPF Responsável: {resp_cpf_msg}")
        
        resultado['formatado']['resp_rg'] = f.formatar_rg(dados.get('resp_rg', ''))
        
        resp_data_rg_fmt, _, _ = f.formatar_data(dados.get('resp_data_rg'))
        resultado['formatado']['resp_data_rg'] = resp_data_rg_fmt
        
        resp_nasc_fmt, _, _ = f.formatar_data(dados.get('resp_nascimento'))
        resultado['formatado']['resp_nascimento'] = resp_nasc_fmt
    
    # Status final
    resultado['erros'] = erros
    resultado['avisos'] = avisos
    
    if erros:
        resultado['status'] = 'ERRO'
    elif avisos:
        resultado['status'] = 'AVISO'
    else:
        resultado['status'] = 'OK'
    
    return resultado


# Testes
if __name__ == "__main__":
    f = FormatadorPlanilha
    
    print("=== TESTES DE FORMATAÇÃO ===\n")
    
    # Nomes
    nomes_teste = [
        "PEDRO HENRIQUE DA SILVA",
        "maria jose dos santos",
        "JOÃO",
        "ANA CLARA DE OLIVEIRA COSTA SANTOS",
        "josé das neves",
    ]
    print("NOMES:")
    for nome in nomes_teste:
        fmt, ok, msg = f.formatar_nome(nome)
        status = "✓" if ok else "✗"
        print(f"  {status} '{nome}' -> '{fmt}' {msg}")
    
    print("\nCPFs:")
    cpfs_teste = [
        "964.887.274-00",
        "11111111111",
        "529.982.247-25",
        "12345678901",
    ]
    for cpf in cpfs_teste:
        fmt, ok, msg = f.formatar_cpf(cpf)
        status = "✓" if ok else "✗"
        print(f"  {status} '{cpf}' -> '{fmt}' {msg}")
    
    print("\nTELEFONES:")
    tels_teste = [
        "71 9 8112 8637",
        "71982432713",
        "99887766",
        "7199988664",
    ]
    for tel in tels_teste:
        fmt, ok, msg = f.formatar_telefone(tel)
        status = "✓" if ok else "✗"
        print(f"  {status} '{tel}' -> '{fmt}' {msg}")
