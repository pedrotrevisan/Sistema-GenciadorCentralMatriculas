"""Serviço de envio de emails via Resend"""
import os
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Importar resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Biblioteca 'resend' não instalada. Execute: pip install resend")


class EmailService:
    """Serviço para envio de emails via Resend"""
    
    def __init__(self):
        self.api_key = os.environ.get('RESEND_API_KEY', '')
        self.from_email = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        self.from_name = os.environ.get('RESEND_FROM_NAME', 'SYNAPSE - Sistema de Matrículas')
        self.enabled = bool(self.api_key and RESEND_AVAILABLE)
        
        if self.enabled:
            resend.api_key = self.api_key
            logger.info("Serviço de email Resend configurado com sucesso!")
        else:
            if not RESEND_AVAILABLE:
                logger.warning("Resend não disponível - biblioteca não instalada")
            elif not self.api_key:
                logger.warning("Serviço de email não configurado. Defina RESEND_API_KEY no .env")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Envia um email via Resend
        
        Args:
            to_email: Email do destinatário
            subject: Assunto do email
            body_html: Corpo do email em HTML
            body_text: Corpo do email em texto simples (opcional)
            cc: Lista de emails em cópia (opcional)
            bcc: Lista de emails em cópia oculta (opcional)
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.enabled:
            logger.warning(f"Email não enviado (serviço desabilitado): {subject} -> {to_email}")
            return False
        
        try:
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": body_html,
            }
            
            if body_text:
                params["text"] = body_text
            
            if cc:
                params["cc"] = cc
            
            if bcc:
                params["bcc"] = bcc
            
            response = resend.Emails.send(params)
            
            logger.info(f"Email enviado com sucesso: {subject} -> {to_email} (ID: {response.get('id', 'N/A')})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def send_atribuicao_notification(
        self,
        to_email: str,
        to_name: str,
        tipo_demanda: str,
        titulo_demanda: str,
        descricao: str,
        prioridade: str,
        link: str,
        atribuido_por: str
    ) -> bool:
        """
        Envia notificação de nova atribuição
        """
        subject = f"[SYNAPSE] Nova demanda atribuída: {titulo_demanda}"
        
        prioridade_emoji = {
            'urgente': '🔴',
            'alta': '🟠',
            'normal': '🔵',
            'baixa': '⚪'
        }.get(prioridade, '🔵')
        
        prioridade_color = {
            'urgente': '#dc2626',
            'alta': '#ea580c',
            'normal': '#2563eb',
            'baixa': '#6b7280'
        }.get(prioridade, '#2563eb')
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #004587, #0066cc); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📥 Nova Demanda Atribuída</h1>
                </div>
                <div style="padding: 30px;">
                    <p style="font-size: 16px;">Olá, <strong>{to_name}</strong>!</p>
                    <p style="color: #666;">Uma nova demanda foi atribuída a você no sistema SYNAPSE.</p>
                    
                    <div style="background: #f8f9fa; border-left: 4px solid #004587; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                        <p style="margin: 0 0 10px 0;">
                            <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #e3f2fd; color: #1565c0; margin-right: 8px;">{tipo_demanda.upper()}</span>
                            <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: {prioridade_color}22; color: {prioridade_color};">{prioridade_emoji} {prioridade.upper()}</span>
                        </p>
                        <h3 style="margin: 10px 0; color: #333;">{titulo_demanda}</h3>
                        <p style="margin: 0; color: #666;">{descricao}</p>
                    </div>
                    
                    <p><strong>Atribuído por:</strong> {atribuido_por}</p>
                    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                    
                    <a href="{link}" style="display: inline-block; background: #004587; color: white; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-weight: 600; margin-top: 20px;">Acessar Demanda</a>
                </div>
                <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p style="margin: 0;">Este email foi enviado automaticamente pelo sistema SYNAPSE.</p>
                    <p style="margin: 5px 0 0 0;">SENAI CIMATEC - Sistema Central de Matrículas</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
Nova Demanda Atribuída - SYNAPSE

Olá, {to_name}!

Uma nova demanda foi atribuída a você:

Tipo: {tipo_demanda.upper()}
Prioridade: {prioridade.upper()}
Título: {titulo_demanda}
Descrição: {descricao}

Atribuído por: {atribuido_por}
Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Acesse: {link}

---
SENAI CIMATEC - Sistema Central de Matrículas
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_lembrete_notification(
        self,
        to_email: str,
        to_name: str,
        titulo_lembrete: str,
        descricao: str = "",
        link: Optional[str] = None
    ) -> bool:
        """
        Envia notificação de lembrete
        """
        subject = f"[SYNAPSE] Lembrete: {titulo_lembrete}"
        
        link_html = f'<a href="{link}" style="display: inline-block; background: #004587; color: white; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-weight: 600; margin-top: 20px;">Acessar Sistema</a>' if link else ''
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: #ffc107; color: #333; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">🔔 Lembrete</h1>
                </div>
                <div style="padding: 30px;">
                    <p style="font-size: 16px;">Olá, <strong>{to_name}</strong>!</p>
                    
                    <div style="background: #fff8e1; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{titulo_lembrete}</h3>
                        {f'<p style="margin: 0; color: #666;">{descricao}</p>' if descricao else ''}
                    </div>
                    
                    {link_html}
                </div>
                <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p style="margin: 0;">Este email foi enviado automaticamente pelo sistema SYNAPSE.</p>
                    <p style="margin: 5px 0 0 0;">SENAI CIMATEC - Sistema Central de Matrículas</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body_html)


# Instância global do serviço
email_service = EmailService()
