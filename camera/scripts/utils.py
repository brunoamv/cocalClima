#!/usr/bin/env python3
import os
import logging
from datetime import datetime

def load_config():
    """Carrega configurações das variáveis de ambiente"""
    config = {
        # Câmera
        'CAMERA_RTSP_URL': os.getenv('CAMERA_RTSP_URL', 'rtsp://admin:CoraRosa@192.168.69.20:554/cam/realmonitor?channel=1&subtype=0'),
        
        # YouTube
        'YOUTUBE_RTMP_URL': os.getenv('YOUTUBE_RTMP_URL', 'rtmp://a.rtmp.youtube.com/live2'),
        'YOUTUBE_STREAM_KEY': os.getenv('YOUTUBE_STREAM_KEY', 'yx67-vfxc-q2vb-4rkb-402d'),
        
        # Stream
        'STREAM_RESOLUTION': os.getenv('STREAM_RESOLUTION', '1920x1080'),
        'STREAM_FPS': os.getenv('STREAM_FPS', '30'),
        'STREAM_BITRATE': os.getenv('STREAM_BITRATE', '4500k'),
        
        # Telegram
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
        
        # Email
        'SMTP_HOST': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        'SMTP_PORT': os.getenv('SMTP_PORT', '587'),
        'SMTP_USER': os.getenv('SMTP_USER', ''),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', ''),
        'ALERT_EMAIL': os.getenv('ALERT_EMAIL', ''),
        
        # Sistema
        'HEALTH_CHECK_INTERVAL': os.getenv('HEALTH_CHECK_INTERVAL', '30'),
        'RECONNECT_DELAY': os.getenv('RECONNECT_DELAY', '10'),
        'MAX_RECONNECT_ATTEMPTS': os.getenv('MAX_RECONNECT_ATTEMPTS', '3'),
        'ENABLE_FALLBACK': os.getenv('ENABLE_FALLBACK', 'true'),
    }
    
    return config

def setup_logging(log_level=logging.INFO):
    """Configura sistema de logging"""
    # Criar diretório de logs
    log_dir = "/camera/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Nome do arquivo com data
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"stream_{today}.log")
    
    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Retornar logger específico
    logger = logging.getLogger("camera_stream")
    logger.info(f"Logging configurado - arquivo: {log_file}")
    
    return logger

def validate_config(config):
    """Valida configurações essenciais"""
    errors = []
    warnings = []
    
    # Verificações obrigatórias
    if not config['CAMERA_RTSP_URL']:
        errors.append("CAMERA_RTSP_URL não configurado")
    
    if not config['YOUTUBE_RTMP_URL']:
        errors.append("YOUTUBE_RTMP_URL não configurado")
    
    if not config['YOUTUBE_STREAM_KEY']:
        errors.append("YOUTUBE_STREAM_KEY não configurado")
    
    # Verificações de alerta
    if not config['TELEGRAM_BOT_TOKEN'] and not config['SMTP_USER']:
        warnings.append("Nenhum método de alerta configurado (Telegram ou Email)")
    
    if not config['TELEGRAM_BOT_TOKEN']:
        warnings.append("Telegram não configurado")
    
    if not config['SMTP_USER']:
        warnings.append("Email não configurado")
    
    # Verificações de valores numéricos
    try:
        int(config['HEALTH_CHECK_INTERVAL'])
        int(config['RECONNECT_DELAY'])
        int(config['MAX_RECONNECT_ATTEMPTS'])
    except ValueError as e:
        errors.append(f"Valor numérico inválido: {e}")
    
    # Verificar resolução
    if 'x' not in config['STREAM_RESOLUTION']:
        errors.append("STREAM_RESOLUTION deve estar no formato 1920x1080")
    
    # Verificar FPS
    try:
        fps = int(config['STREAM_FPS'])
        if fps <= 0 or fps > 60:
            warnings.append("FPS recomendado entre 1-60")
    except ValueError:
        errors.append("STREAM_FPS deve ser um número")
    
    # Verificar bitrate
    if not config['STREAM_BITRATE'].endswith('k'):
        warnings.append("STREAM_BITRATE deve terminar com 'k' (ex: 4500k)")
    
    return errors, warnings

def format_duration(seconds):
    """Formata duração em segundos para formato legível"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

def format_bytes(bytes_value):
    """Formata bytes para formato legível"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def parse_rtsp_url(rtsp_url):
    """Extrai informações da URL RTSP"""
    try:
        # rtsp://user:pass@host:port/path
        parts = rtsp_url.replace('rtsp://', '').split('/')
        auth_host = parts[0]
        path = '/'.join(parts[1:]) if len(parts) > 1 else ''
        
        if '@' in auth_host:
            auth, host_port = auth_host.split('@')
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user, password = auth, ''
        else:
            user, password = '', ''
            host_port = auth_host
        
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host, port = host_port, '554'
        
        return {
            'user': user,
            'password': password,
            'host': host,
            'port': int(port),
            'path': path,
            'full_url': rtsp_url
        }
    except Exception as e:
        return None

def check_dependencies():
    """Verifica se dependências estão disponíveis"""
    import subprocess
    
    deps = {
        'ffmpeg': False,
        'ffprobe': False,
        'ping': False,
        'curl': False
    }
    
    for dep in deps.keys():
        try:
            result = subprocess.run([dep, '-version'], 
                                  capture_output=True, 
                                  timeout=5)
            deps[dep] = result.returncode == 0
        except:
            deps[dep] = False
    
    return deps

def create_offline_image():
    """Cria imagem offline com Pillow"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Configurações
        width, height = 1920, 1080
        background_color = '#1a1a2e'
        text_color = '#ffffff'
        
        # Criar imagem
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        # Texto principal
        main_text = "Câmera Temporariamente Offline"
        subtitle = "ClimaCocal"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Tentar usar fonte maior
        try:
            # Fonte principal
            font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
            font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            # Fallback para fonte padrão
            font_main = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_time = ImageFont.load_default()
        
        # Calcular posições centralizadas
        bbox_main = draw.textbbox((0, 0), main_text, font=font_main)
        bbox_sub = draw.textbbox((0, 0), subtitle, font=font_sub)
        bbox_time = draw.textbbox((0, 0), timestamp, font=font_time)
        
        main_x = (width - (bbox_main[2] - bbox_main[0])) // 2
        main_y = (height - (bbox_main[3] - bbox_main[1])) // 2 - 50
        
        sub_x = (width - (bbox_sub[2] - bbox_sub[0])) // 2
        sub_y = main_y + 120
        
        time_x = (width - (bbox_time[2] - bbox_time[0])) // 2
        time_y = height - 100
        
        # Desenhar textos
        draw.text((main_x, main_y), main_text, fill=text_color, font=font_main)
        draw.text((sub_x, sub_y), subtitle, fill=text_color, font=font_sub)
        draw.text((time_x, time_y), timestamp, fill='#cccccc', font=font_time)
        
        # Salvar
        output_path = "/camera/static/offline.png"
        image.save(output_path, "PNG")
        
        return True, output_path
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    # Teste das funções
    print("=== Teste das Funções Utils ===")
    
    # Teste de configuração
    config = load_config()
    print(f"Configurações carregadas: {len(config)} itens")
    
    # Validação
    errors, warnings = validate_config(config)
    print(f"Erros: {len(errors)}, Warnings: {len(warnings)}")
    for error in errors:
        print(f"  ❌ {error}")
    for warning in warnings:
        print(f"  ⚠️ {warning}")
    
    # Dependências
    deps = check_dependencies()
    print("Dependências:")
    for dep, available in deps.items():
        print(f"  {dep}: {'✅' if available else '❌'}")
    
    # Parse RTSP
    rtsp_info = parse_rtsp_url(config['CAMERA_RTSP_URL'])
    if rtsp_info:
        print(f"RTSP Host: {rtsp_info['host']}:{rtsp_info['port']}")
    
    # Criar imagem offline
    success, result = create_offline_image()
    print(f"Imagem offline: {'✅' if success else '❌'} {result}")