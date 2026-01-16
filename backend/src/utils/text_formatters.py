"""Utilitários de formatação de texto"""

# Preposições e conjunções que devem permanecer em minúsculo
PREPOSICOES = {'da', 'de', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'para', 'por'}


def formatar_nome_proprio(nome: str) -> str:
    """
    Formata nome próprio para Title Case, mantendo preposições em minúsculo.
    
    Exemplos:
        - "PEDRO HENRIQUE TREVISAN PASSOS COSTA" -> "Pedro Henrique Trevisan Passos Costa"
        - "VALÉRIA CRISTINA DA SILVA PASSOS" -> "Valéria Cristina da Silva Passos"
        - "JOÃO CARLOS DE OLIVEIRA JUNIOR" -> "João Carlos de Oliveira Junior"
    """
    if not nome:
        return nome
    
    # Remove espaços extras e converte para minúsculo
    palavras = nome.strip().lower().split()
    resultado = []
    
    for i, palavra in enumerate(palavras):
        # Primeira palavra sempre capitalizada, preposições em minúsculo no meio
        if i == 0 or palavra not in PREPOSICOES:
            resultado.append(palavra.capitalize())
        else:
            resultado.append(palavra)
    
    return ' '.join(resultado)


def formatar_texto_titulo(texto: str) -> str:
    """
    Formata texto para Title Case simples (todas as palavras capitalizadas).
    Útil para endereços, cidades, etc.
    """
    if not texto:
        return texto
    
    return ' '.join(palavra.capitalize() for palavra in texto.strip().lower().split())
