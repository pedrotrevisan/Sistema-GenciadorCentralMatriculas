"""Templates de Mensagens - E-mail e WhatsApp para CAC SENAI"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class TipoTemplate(Enum):
    """Tipos de templates de mensagem"""
    DOCUMENTOS_PENDENTES = "documentos_pendentes"
    PRAZO_EXPIRANDO = "prazo_expirando"
    CONFIRMACAO_MATRICULA = "confirmacao_matricula"
    AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
    MATRICULA_EFETIVADA = "matricula_efetivada"
    CANCELAMENTO = "cancelamento"
    NAO_ATENDE_REQUISITO = "nao_atende_requisito"
    LEMBRETE_DOCUMENTOS = "lembrete_documentos"


# ==================== TEMPLATES DE E-MAIL ====================

EMAIL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "documentos_pendentes": {
        "assunto": "[SENAI] Documentos Pendentes - Matrícula {protocolo}",
        "corpo_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #004587; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .docs-list {{ background: white; padding: 15px; border-radius: 5px; }}
        .docs-list li {{ margin: 8px 0; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        .btn {{ display: inline-block; background: #E30613; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SENAI CIMATEC</h1>
            <p>Central de Atendimento ao Cliente</p>
        </div>
        <div class="content">
            <p>Olá, <strong>{aluno_nome}</strong>!</p>
            
            <p>Identificamos que sua solicitação de matrícula para o curso <strong>{curso_nome}</strong> 
            está com documentação pendente.</p>
            
            <div class="alert">
                <strong>⚠️ Atenção:</strong> Você tem <strong>{dias_restantes} dias</strong> para regularizar 
                sua documentação. Após esse prazo, sua solicitação poderá ser cancelada automaticamente.
            </div>
            
            <div class="docs-list">
                <p><strong>Documentos pendentes:</strong></p>
                <ul>
                    {documentos_lista}
                </ul>
            </div>
            
            <p>Para enviar seus documentos, você pode:</p>
            <ul>
                <li>Comparecer pessoalmente à CAC</li>
                <li>Enviar por e-mail para cac@senai.br</li>
            </ul>
            
            <p style="text-align: center; margin-top: 20px;">
                <a href="{link_portal}" class="btn">Acessar Portal do Aluno</a>
            </p>
        </div>
        <div class="footer">
            <p>Protocolo: {protocolo}</p>
            <p>Este é um e-mail automático. Em caso de dúvidas, entre em contato com a CAC.</p>
            <p>SENAI CIMATEC - Central de Atendimento ao Cliente</p>
        </div>
    </div>
</body>
</html>
""",
        "corpo_texto": """
SENAI CIMATEC - Central de Atendimento ao Cliente

Olá, {aluno_nome}!

Identificamos que sua solicitação de matrícula para o curso {curso_nome} está com documentação pendente.

⚠️ ATENÇÃO: Você tem {dias_restantes} dias para regularizar sua documentação. 
Após esse prazo, sua solicitação poderá ser cancelada automaticamente.

DOCUMENTOS PENDENTES:
{documentos_lista_texto}

Para enviar seus documentos, você pode:
- Comparecer pessoalmente à CAC
- Enviar por e-mail para cac@senai.br

Protocolo: {protocolo}

Este é um e-mail automático. Em caso de dúvidas, entre em contato com a CAC.
SENAI CIMATEC - Central de Atendimento ao Cliente
"""
    },
    
    "prazo_expirando": {
        "assunto": "[URGENTE] Prazo Expirando - Matrícula {protocolo}",
        "corpo_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #E30613; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .urgente {{ background: #f8d7da; border: 2px solid #E30613; padding: 20px; border-radius: 5px; text-align: center; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 URGENTE</h1>
            <p>Sua matrícula está prestes a ser cancelada</p>
        </div>
        <div class="content">
            <p>Olá, <strong>{aluno_nome}</strong>!</p>
            
            <div class="urgente">
                <h2>⏰ PRAZO EXPIRA {prazo_texto}</h2>
                <p>Sua documentação ainda não foi regularizada.</p>
                <p><strong>Curso:</strong> {curso_nome}</p>
            </div>
            
            <p style="margin-top: 20px;">Se os documentos não forem entregues até o prazo, 
            sua solicitação será <strong>CANCELADA AUTOMATICAMENTE</strong>.</p>
            
            <p>Entre em contato imediatamente com a CAC:</p>
            <ul>
                <li>📞 Telefone: (71) XXXX-XXXX</li>
                <li>📧 E-mail: cac@senai.br</li>
                <li>📍 Presencial: CAC SENAI CIMATEC</li>
            </ul>
        </div>
        <div class="footer">
            <p>Protocolo: {protocolo}</p>
            <p>SENAI CIMATEC - Central de Atendimento ao Cliente</p>
        </div>
    </div>
</body>
</html>
""",
        "corpo_texto": """
🚨 URGENTE - SENAI CIMATEC

Olá, {aluno_nome}!

⏰ PRAZO EXPIRA {prazo_texto}

Sua documentação para o curso {curso_nome} ainda não foi regularizada.

Se os documentos não forem entregues até o prazo, sua solicitação será CANCELADA AUTOMATICAMENTE.

Entre em contato imediatamente com a CAC:
- Telefone: (71) XXXX-XXXX
- E-mail: cac@senai.br
- Presencial: CAC SENAI CIMATEC

Protocolo: {protocolo}
"""
    },
    
    "confirmacao_matricula": {
        "assunto": "[SENAI] Matrícula Aprovada - {curso_nome}",
        "corpo_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .success {{ background: #d4edda; border: 1px solid #28a745; padding: 20px; border-radius: 5px; text-align: center; }}
        .info-box {{ background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        .btn {{ display: inline-block; background: #004587; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ MATRÍCULA APROVADA</h1>
        </div>
        <div class="content">
            <p>Olá, <strong>{aluno_nome}</strong>!</p>
            
            <div class="success">
                <h2>Parabéns! Sua matrícula foi aprovada!</h2>
                <p>Curso: <strong>{curso_nome}</strong></p>
            </div>
            
            <div class="info-box">
                <h3>📋 Informações da Matrícula</h3>
                <p><strong>Protocolo:</strong> {protocolo}</p>
                <p><strong>Turma:</strong> {turma}</p>
                <p><strong>Início:</strong> {data_inicio}</p>
                <p><strong>Horário:</strong> {horario}</p>
                <p><strong>Local:</strong> {local}</p>
            </div>
            
            {info_pagamento}
            
            <p style="text-align: center; margin-top: 20px;">
                <a href="{link_portal}" class="btn">Acessar Portal do Aluno</a>
            </p>
        </div>
        <div class="footer">
            <p>Bem-vindo ao SENAI CIMATEC!</p>
            <p>Em caso de dúvidas, entre em contato com a CAC.</p>
        </div>
    </div>
</body>
</html>
""",
        "corpo_texto": """
✅ MATRÍCULA APROVADA - SENAI CIMATEC

Olá, {aluno_nome}!

Parabéns! Sua matrícula foi aprovada!

INFORMAÇÕES DA MATRÍCULA:
- Curso: {curso_nome}
- Protocolo: {protocolo}
- Turma: {turma}
- Início: {data_inicio}
- Horário: {horario}
- Local: {local}

{info_pagamento_texto}

Bem-vindo ao SENAI CIMATEC!
Em caso de dúvidas, entre em contato com a CAC.
"""
    },
    
    "aguardando_pagamento": {
        "assunto": "[SENAI] Pagamento Pendente - Matrícula {protocolo}",
        "corpo_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #6f42c1; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .payment {{ background: white; padding: 20px; border-radius: 5px; border: 2px solid #6f42c1; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💳 Pagamento Pendente</h1>
        </div>
        <div class="content">
            <p>Olá, <strong>{aluno_nome}</strong>!</p>
            
            <p>Sua documentação foi aprovada! Agora, para efetivar sua matrícula no curso 
            <strong>{curso_nome}</strong>, é necessário realizar o pagamento.</p>
            
            <div class="payment">
                <h3>📋 Dados para Pagamento</h3>
                <p><strong>Valor:</strong> R$ {valor}</p>
                <p><strong>Vencimento:</strong> {data_vencimento}</p>
                <p><strong>Forma de pagamento:</strong> {forma_pagamento}</p>
                {dados_boleto}
            </div>
            
            <p style="margin-top: 20px;"><strong>⚠️ Importante:</strong> A matrícula só será 
            efetivada após a confirmação do pagamento.</p>
        </div>
        <div class="footer">
            <p>Protocolo: {protocolo}</p>
            <p>SENAI CIMATEC - Central de Atendimento ao Cliente</p>
        </div>
    </div>
</body>
</html>
""",
        "corpo_texto": """
💳 PAGAMENTO PENDENTE - SENAI CIMATEC

Olá, {aluno_nome}!

Sua documentação foi aprovada! Para efetivar sua matrícula no curso {curso_nome}, é necessário realizar o pagamento.

DADOS PARA PAGAMENTO:
- Valor: R$ {valor}
- Vencimento: {data_vencimento}
- Forma de pagamento: {forma_pagamento}
{dados_boleto_texto}

⚠️ IMPORTANTE: A matrícula só será efetivada após a confirmação do pagamento.

Protocolo: {protocolo}
SENAI CIMATEC - Central de Atendimento ao Cliente
"""
    },
    
    "nao_atende_requisito": {
        "assunto": "[SENAI] Solicitação Não Aprovada - {curso_nome}",
        "corpo_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .motivo {{ background: #f8d7da; border: 1px solid #dc3545; padding: 20px; border-radius: 5px; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Solicitação Não Aprovada</h1>
        </div>
        <div class="content">
            <p>Olá, <strong>{aluno_nome}</strong>!</p>
            
            <p>Infelizmente, sua solicitação de matrícula para o curso <strong>{curso_nome}</strong> 
            não foi aprovada.</p>
            
            <div class="motivo">
                <h3>📋 Motivo</h3>
                <p>{motivo}</p>
            </div>
            
            <p style="margin-top: 20px;">Se você acredita que houve algum engano ou deseja 
            mais informações, entre em contato com a CAC:</p>
            <ul>
                <li>📧 E-mail: cac@senai.br</li>
                <li>📞 Telefone: (71) XXXX-XXXX</li>
            </ul>
        </div>
        <div class="footer">
            <p>Protocolo: {protocolo}</p>
            <p>SENAI CIMATEC - Central de Atendimento ao Cliente</p>
        </div>
    </div>
</body>
</html>
""",
        "corpo_texto": """
SOLICITAÇÃO NÃO APROVADA - SENAI CIMATEC

Olá, {aluno_nome}!

Infelizmente, sua solicitação de matrícula para o curso {curso_nome} não foi aprovada.

MOTIVO:
{motivo}

Se você acredita que houve algum engano ou deseja mais informações, entre em contato com a CAC:
- E-mail: cac@senai.br
- Telefone: (71) XXXX-XXXX

Protocolo: {protocolo}
SENAI CIMATEC - Central de Atendimento ao Cliente
"""
    }
}


# ==================== TEMPLATES DE WHATSAPP ====================

WHATSAPP_TEMPLATES: Dict[str, Dict[str, str]] = {
    "documentos_pendentes": {
        "mensagem": """🔔 *SENAI CIMATEC - Documentos Pendentes*

Olá, {aluno_nome}!

Sua matrícula no curso *{curso_nome}* está com documentação pendente.

📋 *Documentos faltantes:*
{documentos_lista}

⏰ *Prazo:* {dias_restantes} dias

📍 Compareça à CAC ou envie por e-mail para regularizar.

_Protocolo: {protocolo}_"""
    },
    
    "prazo_expirando": {
        "mensagem": """🚨 *URGENTE - SENAI CIMATEC*

Olá, {aluno_nome}!

⏰ *SEU PRAZO EXPIRA {prazo_texto}!*

Sua documentação para o curso *{curso_nome}* ainda não foi entregue.

❌ Após o prazo, sua solicitação será *CANCELADA*.

📞 Entre em contato IMEDIATAMENTE com a CAC!

_Protocolo: {protocolo}_"""
    },
    
    "confirmacao_matricula": {
        "mensagem": """✅ *MATRÍCULA APROVADA - SENAI CIMATEC*

Olá, {aluno_nome}! 🎉

Sua matrícula foi *APROVADA*!

📚 *Curso:* {curso_nome}
📅 *Início:* {data_inicio}
🕐 *Horário:* {horario}
📍 *Local:* {local}

Bem-vindo ao SENAI CIMATEC!

_Protocolo: {protocolo}_"""
    },
    
    "aguardando_pagamento": {
        "mensagem": """💳 *PAGAMENTO PENDENTE - SENAI CIMATEC*

Olá, {aluno_nome}!

Sua documentação foi aprovada! ✅

Para efetivar a matrícula no curso *{curso_nome}*, realize o pagamento:

💰 *Valor:* R$ {valor}
📅 *Vencimento:* {data_vencimento}

⚠️ A matrícula só será efetivada após o pagamento.

_Protocolo: {protocolo}_"""
    },
    
    "lembrete_documentos": {
        "mensagem": """📋 *LEMBRETE - SENAI CIMATEC*

Olá, {aluno_nome}!

Este é um lembrete sobre sua matrícula no curso *{curso_nome}*.

⏰ *Restam {dias_restantes} dias* para entregar os documentos pendentes.

Regularize sua situação para garantir sua vaga!

_Protocolo: {protocolo}_"""
    }
}


# ==================== FUNÇÕES DE RENDERIZAÇÃO ====================

def render_email_template(
    tipo: str,
    dados: Dict[str, Any],
    formato: str = "html"
) -> Dict[str, str]:
    """
    Renderiza um template de e-mail com os dados fornecidos.
    
    Args:
        tipo: Tipo do template (documentos_pendentes, prazo_expirando, etc)
        dados: Dicionário com os dados para substituição
        formato: "html" ou "texto"
    
    Returns:
        Dict com assunto e corpo do e-mail
    """
    template = EMAIL_TEMPLATES.get(tipo)
    if not template:
        raise ValueError(f"Template de e-mail não encontrado: {tipo}")
    
    assunto = template["assunto"].format(**dados)
    
    if formato == "html":
        corpo = template["corpo_html"].format(**dados)
    else:
        corpo = template["corpo_texto"].format(**dados)
    
    return {
        "assunto": assunto,
        "corpo": corpo,
        "tipo": tipo,
        "formato": formato
    }


def render_whatsapp_template(
    tipo: str,
    dados: Dict[str, Any]
) -> str:
    """
    Renderiza um template de WhatsApp com os dados fornecidos.
    
    Args:
        tipo: Tipo do template
        dados: Dicionário com os dados para substituição
    
    Returns:
        Mensagem formatada para WhatsApp
    """
    template = WHATSAPP_TEMPLATES.get(tipo)
    if not template:
        raise ValueError(f"Template de WhatsApp não encontrado: {tipo}")
    
    return template["mensagem"].format(**dados)


def gerar_link_whatsapp(telefone: str, mensagem: str) -> str:
    """
    Gera link wa.me para envio de mensagem WhatsApp.
    
    Args:
        telefone: Número do telefone (apenas números)
        mensagem: Mensagem a ser enviada
    
    Returns:
        URL do WhatsApp Web
    """
    import urllib.parse
    
    # Limpar telefone (apenas números)
    telefone_limpo = ''.join(filter(str.isdigit, telefone))
    
    # Adicionar código do Brasil se não tiver
    if len(telefone_limpo) == 11:  # DDD + número
        telefone_limpo = "55" + telefone_limpo
    elif len(telefone_limpo) == 10:  # Fixo
        telefone_limpo = "55" + telefone_limpo
    
    # Codificar mensagem
    mensagem_encoded = urllib.parse.quote(mensagem)
    
    return f"https://wa.me/{telefone_limpo}?text={mensagem_encoded}"


def get_templates_disponiveis() -> Dict[str, Any]:
    """Retorna lista de templates disponíveis"""
    return {
        "email": list(EMAIL_TEMPLATES.keys()),
        "whatsapp": list(WHATSAPP_TEMPLATES.keys()),
        "tipos": [t.value for t in TipoTemplate]
    }
