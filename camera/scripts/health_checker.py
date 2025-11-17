#!/usr/bin/env python3
import os
import time
import logging
import subprocess
import socket
from utils import load_config, setup_logging

class CameraHealthChecker:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
        
        # Extrair IP da URL RTSP
        rtsp_url = self.config['CAMERA_RTSP_URL']
        self.camera_ip = self._extract_ip_from_rtsp(rtsp_url)
        self.rtsp_url = rtsp_url
        
        self.logger.info(f"Health Checker configurado para IP: {self.camera_ip}")

    def _extract_ip_from_rtsp(self, rtsp_url):
        """Extrai IP da URL RTSP"""
        try:
            # rtsp://admin:senha@192.168.69.20:554/...
            parts = rtsp_url.split('/')
            auth_host = parts[2]  # admin:senha@192.168.69.20:554

            if '@' in auth_host:
                host_port = auth_host.split('@')[1]  # 192.168.69.20:554
            else:
                host_port = auth_host

            ip = host_port.split(':')[0]  # 192.168.69.20
            return ip
        except Exception as e:
            self.logger.error(f"Erro ao extrair IP da URL RTSP: {e}")
            return "192.168.69.20"  # Fallback

    def ping_camera(self):
        """Testa conectividade com ping"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', self.camera_ip],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Erro no ping: {e}")
            return False

    def test_rtsp_connection(self):
        """Testa conexão RTSP com ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                '-rtsp_transport', 'tcp',
                '-timeout', '10000000',  # 10 segundos em microssegundos
                self.rtsp_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.logger.debug(f"RTSP OK: {result.stdout.strip()}")
                return True
            else:
                self.logger.warning(f"RTSP falhou: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout na conexão RTSP")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao testar RTSP: {e}")
            return False

    def test_socket_connection(self):
        """Testa conectividade via socket (porta 554)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.camera_ip, 554))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.error(f"Erro no teste de socket: {e}")
            return False

    def check_camera_health(self):
        """Executa verificação completa de saúde da câmera"""
        try:
            # Teste 1: Ping
            ping_ok = self.ping_camera()
            if not ping_ok:
                self.logger.warning(f"Ping para {self.camera_ip} falhou")
                return False
            
            # Teste 2: Porta 554 (RTSP)
            socket_ok = self.test_socket_connection()
            if not socket_ok:
                self.logger.warning(f"Conexão socket para {self.camera_ip}:554 falhou")
                return False
            
            # Teste 3: Stream RTSP
            rtsp_ok = self.test_rtsp_connection()
            if not rtsp_ok:
                self.logger.warning("Conexão RTSP falhou")
                return False
            
            self.logger.debug("Câmera saudável")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de saúde: {e}")
            return False

    def get_camera_info(self):
        """Obtém informações detalhadas da câmera"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-rtsp_transport', 'tcp',
                '-timeout', '10000000',
                self.rtsp_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                info = {
                    'streams': len(data.get('streams', [])),
                    'video_streams': 0,
                    'audio_streams': 0,
                    'resolution': 'Unknown',
                    'fps': 'Unknown'
                }
                
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info['video_streams'] += 1
                        info['resolution'] = f"{stream.get('width', '?')}x{stream.get('height', '?')}"
                        
                        # FPS
                        fps_str = stream.get('r_frame_rate', '0/1')
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            if den != '0':
                                fps = int(num) / int(den)
                                info['fps'] = f"{fps:.1f}"
                    
                    elif stream.get('codec_type') == 'audio':
                        info['audio_streams'] += 1
                
                return info
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao obter info da câmera: {e}")
            return None

if __name__ == "__main__":
    # Teste standalone
    checker = CameraHealthChecker()
    print(f"Camera IP: {checker.camera_ip}")
    
    print("Testando ping...")
    ping_result = checker.ping_camera()
    print(f"Ping: {'✅ OK' if ping_result else '❌ FAIL'}")
    
    print("Testando socket...")
    socket_result = checker.test_socket_connection()
    print(f"Socket: {'✅ OK' if socket_result else '❌ FAIL'}")
    
    print("Testando RTSP...")
    rtsp_result = checker.test_rtsp_connection()
    print(f"RTSP: {'✅ OK' if rtsp_result else '❌ FAIL'}")
    
    print("Verificação completa...")
    health = checker.check_camera_health()
    print(f"Saúde: {'✅ SAUDÁVEL' if health else '❌ PROBLEMA'}")
    
    if health:
        print("Obtendo informações da câmera...")
        info = checker.get_camera_info()
        if info:
            print(f"Resolução: {info['resolution']}")
            print(f"FPS: {info['fps']}")
            print(f"Streams de vídeo: {info['video_streams']}")
            print(f"Streams de áudio: {info['audio_streams']}")