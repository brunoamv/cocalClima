#!/usr/bin/env python3
import os
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from stream_manager import StreamManager
from health_checker import CameraHealthChecker
from alert_service import AlertService
from utils import load_config, setup_logging

app = Flask(__name__, template_folder='/camera/templates')

# Instâncias globais
stream_manager = None
health_checker = None
alert_service = None
logger = None

def init_services():
    """Inicializa os serviços"""
    global stream_manager, health_checker, alert_service, logger
    
    logger = setup_logging()
    health_checker = CameraHealthChecker()
    alert_service = AlertService()
    
    # Stream manager será inicializado em thread separada
    logger.info("Dashboard Flask inicializado")

@app.route('/')
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API endpoint para status em tempo real"""
    try:
        # Status da câmera
        camera_online = health_checker.check_camera_health() if health_checker else False
        
        # Status do stream
        stream_status = {
            'streaming': False,
            'stream_mode': 'unknown',
            'reconnect_attempts': 0,
            'uptime_seconds': 0,
            'youtube_video_id': None
        }
        
        if stream_manager:
            stream_status = stream_manager.get_status()
        
        # Informações da câmera
        camera_info = None
        if camera_online and health_checker:
            camera_info = health_checker.get_camera_info()
        
        # Uptime formatado
        uptime_formatted = str(timedelta(seconds=stream_status['uptime_seconds']))
        
        # URL do YouTube
        youtube_url = None
        if stream_status['youtube_video_id']:
            youtube_url = f"https://youtube.com/watch?v={stream_status['youtube_video_id']}"
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'camera': {
                'online': camera_online,
                'ip': health_checker.camera_ip if health_checker else 'Unknown',
                'info': camera_info
            },
            'stream': {
                'active': stream_status['streaming'],
                'mode': stream_status['stream_mode'],
                'reconnect_attempts': stream_status['reconnect_attempts'],
                'uptime': uptime_formatted,
                'uptime_seconds': stream_status['uptime_seconds']
            },
            'youtube': {
                'video_id': stream_status['youtube_video_id'],
                'url': youtube_url
            },
            'system': {
                'ffmpeg_available': check_ffmpeg(),
                'services_initialized': stream_manager is not None
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na API status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def api_start_stream():
    """Inicia o stream"""
    try:
        if not stream_manager:
            return jsonify({'error': 'Stream manager não inicializado'}), 500
        
        # Verifica se já está rodando
        status = stream_manager.get_status()
        if status['streaming']:
            return jsonify({'message': 'Stream já está rodando', 'status': 'already_running'})
        
        # Inicia stream
        camera_healthy = health_checker.check_camera_health()
        mode = "normal" if camera_healthy else "fallback"
        
        success = stream_manager.start_stream(mode)
        
        if success:
            return jsonify({'message': f'Stream {mode} iniciado', 'status': 'started', 'mode': mode})
        else:
            return jsonify({'error': 'Falha ao iniciar stream'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao iniciar stream: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop_stream():
    """Para o stream"""
    try:
        if not stream_manager:
            return jsonify({'error': 'Stream manager não inicializado'}), 500
        
        stream_manager.stop_stream()
        alert_service.send_alert("⏹️ Stream parado via dashboard")
        
        return jsonify({'message': 'Stream parado', 'status': 'stopped'})
        
    except Exception as e:
        logger.error(f"Erro ao parar stream: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart', methods=['POST'])
def api_restart_stream():
    """Reinicia o stream"""
    try:
        if not stream_manager:
            return jsonify({'error': 'Stream manager não inicializado'}), 500
        
        stream_manager.restart_stream()
        alert_service.send_alert("🔄 Stream reiniciado via dashboard")
        
        return jsonify({'message': 'Stream reiniciado', 'status': 'restarted'})
        
    except Exception as e:
        logger.error(f"Erro ao reiniciar stream: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Retorna últimas linhas do log"""
    try:
        log_file = get_latest_log_file()
        if not log_file or not os.path.exists(log_file):
            return jsonify({'logs': ['Nenhum log encontrado']})
        
        # Lê últimas 50 linhas
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
            
        return jsonify({
            'logs': [line.strip() for line in last_lines],
            'log_file': os.path.basename(log_file)
        })
        
    except Exception as e:
        logger.error(f"Erro ao ler logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-alerts', methods=['POST'])
def api_test_alerts():
    """Testa sistema de alertas"""
    try:
        if not alert_service:
            return jsonify({'error': 'Alert service não inicializado'}), 500
        
        # Testa Telegram
        telegram_ok, telegram_msg = alert_service.test_telegram()
        
        # Testa Email
        email_ok, email_msg = alert_service.test_email()
        
        return jsonify({
            'telegram': {
                'ok': telegram_ok,
                'message': telegram_msg
            },
            'email': {
                'ok': email_ok,
                'message': email_msg
            },
            'overall': telegram_ok or email_ok
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar alertas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera-test')
def api_camera_test():
    """Testa conectividade com a câmera"""
    try:
        if not health_checker:
            return jsonify({'error': 'Health checker não inicializado'}), 500
        
        ping_ok = health_checker.ping_camera()
        socket_ok = health_checker.test_socket_connection()
        rtsp_ok = health_checker.test_rtsp_connection()
        
        return jsonify({
            'ping': ping_ok,
            'socket': socket_ok,
            'rtsp': rtsp_ok,
            'overall': ping_ok and socket_ok and rtsp_ok,
            'camera_ip': health_checker.camera_ip
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar câmera: {e}")
        return jsonify({'error': str(e)}), 500

def check_ffmpeg():
    """Verifica se FFmpeg está disponível"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def get_latest_log_file():
    """Encontra o arquivo de log mais recente"""
    try:
        log_dir = "/camera/logs"
        if not os.path.exists(log_dir):
            return None
        
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if not log_files:
            return None
        
        # Ordena por data de modificação
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
        return os.path.join(log_dir, log_files[0])
        
    except:
        return None

def start_stream_manager_thread():
    """Inicia stream manager em thread separada"""
    global stream_manager
    
    time.sleep(5)  # Aguarda Flask inicializar
    
    try:
        stream_manager = StreamManager()
        logger.info("Iniciando Stream Manager em background...")
        stream_manager.monitor_loop()
    except Exception as e:
        logger.error(f"Erro no Stream Manager: {e}")

if __name__ == '__main__':
    # Inicializa serviços
    init_services()
    
    # Inicia stream manager em thread separada
    stream_thread = threading.Thread(target=start_stream_manager_thread, daemon=True)
    stream_thread.start()
    
    # Inicia Flask
    app.run(host='0.0.0.0', port=8001, debug=False)