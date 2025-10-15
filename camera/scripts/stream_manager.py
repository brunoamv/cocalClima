#!/usr/bin/env python3
import os
import sys
import time
import logging
import subprocess
import threading
from datetime import datetime
from health_checker import CameraHealthChecker
from alert_service import AlertService
from utils import load_config, setup_logging

class StreamManager:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
        self.health_checker = CameraHealthChecker()
        self.alert_service = AlertService()
        
        self.ffmpeg_process = None
        self.is_streaming = False
        self.stream_mode = "normal"  # normal | fallback
        self.reconnect_attempts = 0
        self.start_time = datetime.now()
        
        # Configurações
        self.rtsp_url = self.config['CAMERA_RTSP_URL']
        self.rtmp_url = self.config['YOUTUBE_RTMP_URL']
        self.stream_key = self.config['YOUTUBE_STREAM_KEY']
        self.max_attempts = int(self.config['MAX_RECONNECT_ATTEMPTS'])
        self.reconnect_delay = int(self.config['RECONNECT_DELAY'])
        self.fallback_enabled = self.config['ENABLE_FALLBACK'].lower() == 'true'

    def get_youtube_video_id(self):
        """Lê YOUTUBE_VIDEO_ID do views.py Django"""
        try:
            views_file = "/app/myproject/core/views.py"
            with open(views_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip().startswith('YOUTUBE_VIDEO_ID'):
                        # Extrai o ID entre aspas
                        return line.split('"')[1]
            return None
        except Exception as e:
            self.logger.error(f"Erro ao ler YOUTUBE_VIDEO_ID: {e}")
            return None

    def build_ffmpeg_command(self, mode="normal"):
        """Constrói comando FFmpeg"""
        base_cmd = [
            'ffmpeg', '-y', '-re'
        ]
        
        if mode == "normal":
            # Stream normal da câmera
            base_cmd.extend([
                '-rtsp_transport', 'tcp',
                '-i', self.rtsp_url
            ])
        else:
            # Fallback com imagem estática
            base_cmd.extend([
                '-loop', '1',
                '-framerate', '30',
                '-i', '/camera/static/offline.png'
            ])
        
        # Configurações de vídeo
        base_cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-b:v', self.config['STREAM_BITRATE'],
            '-maxrate', self.config['STREAM_BITRATE'],
            '-bufsize', '9000k',
            '-s', self.config['STREAM_RESOLUTION'],
            '-r', self.config['STREAM_FPS'],
            '-g', '60',
            '-pix_fmt', 'yuv420p'
        ])
        
        # Configurações de áudio
        if mode == "normal":
            base_cmd.extend([
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100'
            ])
        else:
            # Sem áudio no fallback
            base_cmd.extend([
                '-f', 'lavfi',
                '-i', 'anullsrc',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100'
            ])
        
        # Saída RTMP
        base_cmd.extend([
            '-f', 'flv',
            f'{self.rtmp_url}/{self.stream_key}'
        ])
        
        return base_cmd

    def start_stream(self, mode="normal"):
        """Inicia o stream FFmpeg"""
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.logger.warning("Stream já está rodando")
            return False
        
        try:
            cmd = self.build_ffmpeg_command(mode)
            self.logger.info(f"Iniciando stream {mode}: {' '.join(cmd[:8])}...")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.is_streaming = True
            self.stream_mode = mode
            
            # Thread para monitorar saída do FFmpeg
            threading.Thread(target=self._monitor_ffmpeg_output, daemon=True).start()
            
            video_id = self.get_youtube_video_id()
            msg = f"🎬 Stream {mode} iniciado"
            if video_id:
                msg += f"\n📺 YouTube: https://youtube.com/watch?v={video_id}"
            
            self.alert_service.send_alert(msg)
            self.logger.info(f"Stream {mode} iniciado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar stream: {e}")
            self.alert_service.send_alert(f"❌ Erro ao iniciar stream: {e}")
            return False

    def stop_stream(self):
        """Para o stream FFmpeg"""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
                self.ffmpeg_process.wait()
            
            self.ffmpeg_process = None
            self.is_streaming = False
            self.logger.info("Stream parado")

    def _monitor_ffmpeg_output(self):
        """Monitora saída do FFmpeg para detectar erros"""
        if not self.ffmpeg_process:
            return
        
        try:
            for line in iter(self.ffmpeg_process.stderr.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                if line:
                    # Log apenas erros importantes
                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'connection']):
                        self.logger.warning(f"FFmpeg: {line}")
                    
                    # Detecta desconexão
                    if 'connection failed' in line.lower() or 'broken pipe' in line.lower():
                        self.logger.error("Detectada desconexão do stream")
                        self._handle_stream_failure()
                        break
        except Exception as e:
            self.logger.error(f"Erro ao monitorar FFmpeg: {e}")

    def _handle_stream_failure(self):
        """Lida com falha do stream"""
        self.is_streaming = False
        self.alert_service.send_alert("⚠️ Stream caiu, tentando reconectar...")
        
        # Aguarda antes de tentar reconectar
        time.sleep(self.reconnect_delay)
        
        # Tenta reconectar
        self.reconnect_attempts += 1
        if self.reconnect_attempts <= self.max_attempts:
            self.logger.info(f"Tentativa de reconexão {self.reconnect_attempts}/{self.max_attempts}")
            self.restart_stream()
        else:
            self.logger.error("Máximo de tentativas de reconexão atingido")
            self.alert_service.send_alert("❌ Falha ao reconectar stream após múltiplas tentativas")

    def restart_stream(self):
        """Reinicia o stream"""
        self.stop_stream()
        time.sleep(2)
        
        # Verifica saúde da câmera
        is_healthy = self.health_checker.check_camera_health()
        
        if is_healthy:
            success = self.start_stream("normal")
            if success:
                self.reconnect_attempts = 0  # Reset contador
        else:
            if self.fallback_enabled:
                self.logger.info("Câmera offline, iniciando fallback")
                self.start_stream("fallback")
            else:
                self.logger.error("Câmera offline e fallback desabilitado")

    def get_status(self):
        """Retorna status atual do stream"""
        camera_status = self.health_checker.check_camera_health()
        uptime = datetime.now() - self.start_time
        
        return {
            'streaming': self.is_streaming,
            'stream_mode': self.stream_mode,
            'camera_online': camera_status,
            'reconnect_attempts': self.reconnect_attempts,
            'uptime_seconds': int(uptime.total_seconds()),
            'youtube_video_id': self.get_youtube_video_id()
        }

    def monitor_loop(self):
        """Loop principal de monitoramento"""
        self.logger.info("Iniciando Stream Manager")
        self.alert_service.send_alert("🎬 Stream Manager Iniciado")
        
        last_camera_status = None
        
        while True:
            try:
                # Verifica saúde da câmera
                camera_healthy = self.health_checker.check_camera_health()
                
                # Detecta mudanças no status da câmera
                if last_camera_status is not None and last_camera_status != camera_healthy:
                    if camera_healthy:
                        self.alert_service.send_alert("📷 Câmera Online")
                        if self.stream_mode == "fallback":
                            self.logger.info("Câmera voltou, mudando para stream normal")
                            self.restart_stream()
                    else:
                        self.alert_service.send_alert("❌ Câmera Offline")
                        if self.stream_mode == "normal" and self.fallback_enabled:
                            self.logger.info("Câmera caiu, mudando para fallback")
                            self.restart_stream()
                
                last_camera_status = camera_healthy
                
                # Verifica se o stream está rodando
                if not self.is_streaming:
                    self.logger.info("Stream não está rodando, iniciando...")
                    self.restart_stream()
                
                # Verifica se processo FFmpeg ainda está vivo
                if self.ffmpeg_process and self.ffmpeg_process.poll() is not None:
                    self.logger.warning("Processo FFmpeg morreu")
                    self._handle_stream_failure()
                
                time.sleep(int(self.config['HEALTH_CHECK_INTERVAL']))
                
            except KeyboardInterrupt:
                self.logger.info("Interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(30)  # Aguarda antes de tentar novamente
        
        self.stop_stream()
        self.logger.info("Stream Manager finalizado")

if __name__ == "__main__":
    manager = StreamManager()
    try:
        manager.monitor_loop()
    except KeyboardInterrupt:
        print("\nParando Stream Manager...")
        manager.stop_stream()
        sys.exit(0)