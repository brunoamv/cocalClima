#!/usr/bin/env python3
import os
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import load_config, setup_logging

class AlertService:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
        
        # Configurações Telegram
        self.telegram_token = self.config.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = self.config.get('TELEGRAM_CHAT_ID')
        
        # Configurações Email
        self.smtp_host = self.config.get('SMTP_HOST')
        self.smtp_port = int(self.config.get('SMTP_PORT', 587))
        self.smtp_user = self.config.get('SMTP_USER')
        self.smtp_password = self.config.get('SMTP_PASSWORD')
        self.alert_email = self.config.get('ALERT_EMAIL')
        
        # Cooldown para evitar spam (5 minutos)
        self.cooldown_minutes = 5
        self.last_alerts = {}

    def _is_in_cooldown(self, alert_type):
        """Verifica se o tipo de alerta está em cooldown"""
        if alert_type not in self.last_alerts:
            return False
        
        last_time = self.last_alerts[alert_type]
        now = datetime.now()
        
        if (now - last_time) > timedelta(minutes=self.cooldown_minutes):
            return False
        
        return True

    def _update_cooldown(self, alert_type):
        """Atualiza timestamp do cooldown"""
        self.last_alerts[alert_type] = datetime.now()

    def send_telegram_alert(self, message):
        """Envia alerta via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.debug("Telegram não configurado")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # Adiciona timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"🎥 ClimaCocal Stream\n{timestamp}\n\n{message}"
            
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': full_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Alerta Telegram enviado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Telegram: {e}")
            return False

    def send_email_alert(self, subject, message):
        """Envia alerta via email"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.alert_email]):
            self.logger.debug("Email não configurado")
            return False
        
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email
            msg['Subject'] = f"ClimaCocal Stream - {subject}"
            
            # Corpo do email
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            body = f"""
ClimaCocal Camera Stream Alert

Timestamp: {timestamp}
Subject: {subject}

Message:
{message}

---
Camera Stream System
ClimaCocal
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_user, self.alert_email, text)
            server.quit()
            
            self.logger.info("Alerta email enviado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
            return False

    def send_alert(self, message, alert_type="general"):
        """Envia alerta via todos os canais configurados"""
        # Verifica cooldown
        if self._is_in_cooldown(alert_type):
            self.logger.debug(f"Alerta {alert_type} em cooldown")
            return
        
        self.logger.info(f"Enviando alerta: {message}")
        
        # Determina subject baseado no tipo
        subject_map = {
            "camera_offline": "Câmera Offline",
            "camera_online": "Câmera Online",
            "stream_failed": "Stream Falhou",
            "stream_started": "Stream Iniciado",
            "system_error": "Erro do Sistema",
            "general": "Notificação"
        }
        
        subject = subject_map.get(alert_type, "Alerta")
        
        # Enviar via Telegram
        telegram_ok = self.send_telegram_alert(message)
        
        # Enviar via Email
        email_ok = self.send_email_alert(subject, message)
        
        # Atualizar cooldown apenas se pelo menos um método funcionou
        if telegram_ok or email_ok:
            self._update_cooldown(alert_type)
        
        return telegram_ok or email_ok

    def test_telegram(self):
        """Testa configuração do Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return False, "Token ou Chat ID não configurados"
        
        try:
            # Teste de conectividade com a API
            url = f"https://api.telegram.org/bot{self.telegram_token}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if not bot_info.get('ok'):
                return False, "Token inválido"
            
            # Teste de envio
            test_result = self.send_telegram_alert("🧪 Teste de configuração do Telegram")
            
            if test_result:
                return True, f"OK - Bot: {bot_info['result']['username']}"
            else:
                return False, "Falha ao enviar mensagem de teste"
                
        except Exception as e:
            return False, f"Erro: {e}"

    def test_email(self):
        """Testa configuração do email"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.alert_email]):
            return False, "Configurações SMTP incompletas"
        
        try:
            # Teste de conectividade SMTP
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            
            # Teste de envio
            test_result = self.send_email_alert(
                "Teste de Configuração",
                "Este é um teste da configuração de email do sistema de streaming."
            )
            
            if test_result:
                return True, f"OK - SMTP: {self.smtp_host}:{self.smtp_port}"
            else:
                return False, "Falha ao enviar email de teste"
                
        except Exception as e:
            return False, f"Erro SMTP: {e}"

    def send_startup_alert(self):
        """Envia alerta de inicialização do sistema"""
        self.send_alert("🎬 Stream Manager Iniciado", "system_startup")

    def send_camera_status_alert(self, is_online):
        """Envia alerta de mudança de status da câmera"""
        if is_online:
            self.send_alert("📷 Câmera Online", "camera_online")
        else:
            self.send_alert("❌ Câmera Offline", "camera_offline")

    def send_stream_status_alert(self, status, mode="normal"):
        """Envia alerta de status do stream"""
        if status == "started":
            msg = f"🎬 Stream {mode} iniciado"
            self.send_alert(msg, "stream_started")
        elif status == "failed":
            self.send_alert("⚠️ Stream falhou", "stream_failed")
        elif status == "reconnecting":
            self.send_alert("🔄 Tentando reconectar stream", "stream_failed")

    def send_error_alert(self, error_message):
        """Envia alerta de erro do sistema"""
        self.send_alert(f"❌ Erro: {error_message}", "system_error")

if __name__ == "__main__":
    # Teste standalone
    alert = AlertService()
    
    print("Testando Telegram...")
    telegram_ok, telegram_msg = alert.test_telegram()
    print(f"Telegram: {'✅' if telegram_ok else '❌'} {telegram_msg}")
    
    print("Testando Email...")
    email_ok, email_msg = alert.test_email()
    print(f"Email: {'✅' if email_ok else '❌'} {email_msg}")
    
    if telegram_ok or email_ok:
        print("Enviando alerta de teste...")
        alert.send_alert("🧪 Teste completo do sistema de alertas")
    else:
        print("❌ Nenhum método de alerta configurado corretamente")