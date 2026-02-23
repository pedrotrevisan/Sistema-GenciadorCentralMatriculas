"""Serviço de envio de emails via SMTP Outlook/Microsoft 365"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Serviço para envio de emails via SMTP"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.office365.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('SMTP_FROM_EMAIL', self.smtp_user)
        self.from_name = os.environ.get('SMTP_FROM_NAME', 'SYNAPSE - Sistema de Matrículas')
        self.enabled = bool(self.smtp_user and self.smtp_password)
        
        if not self.enabled:
            logger.warning("Serviço de email não configurado. Defina SMTP_USER e SMTP_PASSWORD no .env")
    
    def _get_connection(self):
        """Estabelece conexão com o servidor SMTP"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Erro ao conectar ao servidor SMTP: {e}")
            raise
    
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
        Envia um email
        
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
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Adiciona corpo texto
            if body_text:
                part1 = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Adiciona corpo HTML
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)
            
            # Lista de todos os destinatários
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Envia
            server = self._get_connection()
            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Email enviado com sucesso: {subject} -> {to_email}")
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
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #004587, #0066cc); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
                .badge-tipo {{ background: #e3f2fd; color: #1565c0; }}
                .badge-prioridade {{ background: #fff3e0; color: #e65100; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #004587; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }}
                .btn {{ display: inline-block; background: #004587; color: white; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
                .btn:hover {{ background: #003366; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Nova Demanda Atribuída</h1>
                </div>
                <div class="content">
                    <p>Olá, <strong>{to_name}</strong>!</p>
                    <p>Uma nova demanda foi atribuída a você no sistema SYNAPSE.</p>
                    
                    <div class="info-box">
                        <p style="margin: 0 0 10px 0;">
                            <span class="badge badge-tipo">{tipo_demanda.upper()}</span>
                            <span class="badge badge-prioridade">{prioridade_emoji} {prioridade.upper()}</span>
                        </p>
                        <h3 style="margin: 0 0 10px 0; color: #333;">{titulo_demanda}</h3>
                        <p style="margin: 0; color: #666;">{descricao}</p>
                    </div>
                    
                    <p><strong>Atribuído por:</strong> {atribuido_por}</p>
                    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                    
                    <a href="{link}" class="btn">Acessar Demanda</a>
                </div>
                <div class="footer">
                    <p>Este email foi enviado automaticamente pelo sistema SYNAPSE.</p>
                    <p>SENAI CIMATEC - Sistema Central de Matrículas</p>
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
        
        link_html = f'<a href="{link}" class="btn">Acessar Sistema</a>' if link else ''
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #ffc107; color: #333; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #fff8e1; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }}
                .btn {{ display: inline-block; background: #004587; color: white; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Lembrete</h1>
                </div>
                <div class="content">
                    <p>Olá, <strong>{to_name}</strong>!</p>
                    
                    <div class="info-box">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{titulo_lembrete}</h3>
                        {f'<p style="margin: 0; color: #666;">{descricao}</p>' if descricao else ''}
                    </div>
                    
                    {link_html}
                </div>
                <div class="footer">
                    <p>Este email foi enviado automaticamente pelo sistema SYNAPSE.</p>
                    <p>SENAI CIMATEC - Sistema Central de Matrículas</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body_html)


# Instância global do serviço
email_service = EmailService()
