"""
Direct Camera Streaming Service
Handles FFmpeg-based RTSP to HLS conversion with payment validation
"""
import os
import subprocess
import threading
import time
import logging
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CameraStreamingService:
    """Direct camera streaming service with payment validation"""
    
    def __init__(self):
        self.rtsp_url = os.environ.get(
            'CAMERA_RTSP_URL', 
            'rtsp://admin:CoraRosa@192.168.3.62:554/cam/realmonitor?channel=1&subtype=0'
        )
        self.stream_output_dir = Path('/app/camera_stream')
        self.stream_output_dir.mkdir(exist_ok=True)
        
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.is_streaming = False
        self.last_segment_time = 0
        self.last_restart_time = 0  # Cooldown para evitar restart excessivo
        
        # Stream configuration
        self.stream_config = {
            'resolution': '1280x720',
            'fps': '20',
            'bitrate': '2500k',
            'segment_duration': 3,  # seconds
            'playlist_length': 10   # segments
        }
    
    def test_camera_connection(self) -> bool:
        """Test if camera stream is available by checking existing stream files"""
        try:
            # Check if stream.m3u8 exists and is recent (within last 30 seconds)
            playlist_path = self.stream_output_dir / 'stream.m3u8'
            
            if playlist_path.exists():
                # Check if file is recent
                file_age = time.time() - playlist_path.stat().st_mtime
                
                if file_age < 30:  # File is recent (less than 30 seconds old)
                    cache.set('camera_status', 'online', timeout=30)
                    logger.info("Camera connection test: SUCCESS (stream files detected)")
                    return True
                else:
                    logger.warning(f"Stream playlist exists but is old ({file_age:.1f}s)")
                    # Auto-restart stream if playlist is too old (>90 seconds) and cooldown passed
                    if file_age > 90:
                        current_time = time.time()
                        if current_time - self.last_restart_time > 300:  # 5 min cooldown
                            logger.info("Auto-restarting stream due to old playlist")
                            self.last_restart_time = current_time
                            self.restart_stream()
                        else:
                            logger.debug(f"Restart cooldown active ({(current_time - self.last_restart_time):.0f}s)")
            
            # If no recent playlist, try direct camera test (fallback)
            try:
                test_cmd = [
                    'ffprobe', '-v', 'quiet', '-rtsp_transport', 'tcp',
                    '-i', self.rtsp_url, '-show_entries', 'stream=codec_type',
                    '-of', 'csv=p=0'
                ]
                
                result = subprocess.run(
                    test_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                
                camera_accessible = 'video' in result.stdout
                cache.set('camera_status', 'online' if camera_accessible else 'offline', timeout=30)
                
                logger.info(f"Camera direct test: {'SUCCESS' if camera_accessible else 'FAILED'}")
                return camera_accessible
                
            except FileNotFoundError:
                # ffprobe not available, but we can still check stream files
                logger.warning("ffprobe not available, using stream file detection only")
                cache.set('camera_status', 'unknown', timeout=30)
                return False
            
        except Exception as e:
            logger.error(f"Camera connection test failed: {e}")
            cache.set('camera_status', 'error', timeout=30)
            return False
    
    def get_ffmpeg_command(self) -> list:
        """Generate optimized FFmpeg command for HLS streaming"""
        playlist_path = self.stream_output_dir / 'stream.m3u8'
        segment_pattern = self.stream_output_dir / 'segment_%03d.ts'
        
        return [
            'ffmpeg',
            '-y',  # Overwrite output
            '-v', 'error',  # Minimal logging
            
            # Input settings
            '-rtsp_transport', 'tcp',
            '-i', self.rtsp_url,
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            
            # Video encoding
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-profile:v', 'baseline',
            '-level', '3.1',
            
            # Video quality
            '-s', self.stream_config['resolution'],
            '-r', self.stream_config['fps'],
            '-b:v', self.stream_config['bitrate'],
            '-maxrate', '2800k',
            '-bufsize', '5000k',
            
            # Keyframe settings
            '-g', '40',  # Keyframe every 2 seconds
            '-keyint_min', '20',
            '-sc_threshold', '0',
            
            # Audio (if available)
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            
            # HLS output
            '-f', 'hls',
            '-hls_time', str(self.stream_config['segment_duration']),
            '-hls_list_size', str(self.stream_config['playlist_length']),
            '-hls_flags', 'delete_segments',
            '-hls_segment_filename', str(segment_pattern),
            str(playlist_path)
        ]
    
    def start_streaming(self) -> bool:
        """Start FFmpeg streaming process"""
        if self.is_streaming:
            logger.warning("Streaming already active")
            return True
            
        if not self.test_camera_connection():
            logger.error("Cannot start streaming: camera not accessible")
            return False
        
        try:
            cmd = self.get_ffmpeg_command()
            logger.info(f"Starting FFmpeg with command: {' '.join(cmd)}")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.is_streaming = True
            self.last_segment_time = time.time()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_stream, daemon=True)
            monitor_thread.start()
            
            cache.set('streaming_status', 'active', timeout=300)
            logger.info(f"FFmpeg streaming started (PID: {self.ffmpeg_process.pid})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            self.is_streaming = False
            return False
    
    def stop_streaming(self) -> bool:
        """Stop FFmpeg streaming process"""
        if not self.is_streaming or not self.ffmpeg_process:
            logger.info("No active streaming to stop")
            return True
            
        try:
            logger.info("Stopping FFmpeg streaming...")
            self.ffmpeg_process.terminate()
            
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("FFmpeg didn't terminate gracefully, killing...")
                self.ffmpeg_process.kill()
                self.ffmpeg_process.wait()
            
            self.is_streaming = False
            self.ffmpeg_process = None
            
            # Cleanup stream files
            self._cleanup_stream_files()
            
            cache.set('streaming_status', 'stopped', timeout=300)
            logger.info("FFmpeg streaming stopped successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")
            return False
    
    def restart_stream(self) -> bool:
        """Restart streaming process (stop + start)"""
        try:
            logger.info("Restarting stream...")
            
            # Stop current stream
            if self.is_streaming:
                self.stop_streaming()
                time.sleep(2)  # Brief pause
            
            # Start fresh stream
            result = self.start_streaming()
            
            # Handle both dict and bool return types
            if isinstance(result, dict):
                success = result.get('success', False)
                message = result.get('message', 'Unknown error')
            else:
                success = bool(result)
                message = 'Start streaming returned boolean'
            
            if success:
                logger.info("Stream restart successful")
                return True
            else:
                logger.error(f"Stream restart failed: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Error during stream restart: {e}")
            return False
    
    def _monitor_stream(self):
        """Monitor streaming process health and auto-restart if needed"""
        while self.is_streaming and self.ffmpeg_process:
            try:
                # Check if process is still running
                if self.ffmpeg_process.poll() is not None:
                    logger.error("FFmpeg process terminated unexpectedly")
                    self.is_streaming = False
                    cache.set('streaming_status', 'error', timeout=300)
                    break
                
                # Check if segments are being created
                playlist_path = self.stream_output_dir / 'stream.m3u8'
                if playlist_path.exists():
                    current_time = time.time()
                    if current_time - self.last_segment_time < 30:  # Segments should be created every 3s
                        self.last_segment_time = current_time
                    else:
                        logger.warning("No new segments detected, stream may be stalled")
                        # Auto-restart if stream has been stalled for >60 seconds and cooldown passed
                        file_age = current_time - playlist_path.stat().st_mtime
                        if file_age > 60 and current_time - self.last_restart_time > 300:
                            logger.info("Auto-restarting stalled stream")
                            self.last_restart_time = current_time
                            self.restart_stream()
                            break
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Stream monitoring error: {e}")
                break
    
    def _cleanup_stream_files(self):
        """Clean up HLS stream files"""
        try:
            for file_path in self.stream_output_dir.glob('*'):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("Stream files cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up stream files: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current streaming status"""
        camera_status = cache.get('camera_status', 'unknown')
        streaming_status = cache.get('streaming_status', 'stopped')
        playlist_path = self.stream_output_dir / 'stream.m3u8'
        playlist_exists = playlist_path.exists()
        
        # Check if stream is actually running by examining files
        stream_active = False
        external_stream_detected = False
        
        if playlist_exists:
            try:
                file_age = time.time() - playlist_path.stat().st_mtime
                stream_active = file_age < 30  # Recent playlist indicates active stream
                external_stream_detected = stream_active and not self.is_streaming
                
                # If we detect active external streaming, update our status
                if external_stream_detected:
                    logger.info("External streaming detected, updating status")
                    streaming_status = 'active'
                    cache.set('streaming_status', 'active', timeout=300)
                    
            except Exception as e:
                logger.error(f"Error checking playlist age: {e}")
        
        # Final status determination
        is_streaming_final = self.is_streaming or stream_active
        streaming_status_final = 'active' if is_streaming_final else 'stopped'
        
        return {
            'is_streaming': is_streaming_final,
            'camera_status': camera_status,
            'streaming_status': streaming_status_final,
            'playlist_available': playlist_exists,
            'process_active': self.ffmpeg_process is not None and self.ffmpeg_process.poll() is None,
            'stream_config': self.stream_config,
            'external_stream_detected': external_stream_detected
        }


class PaymentValidationService:
    """Service for validating payment status for camera access"""
    
    @staticmethod
    def check_payment_status() -> str:
        """Check current payment status from cache"""
        return cache.get("payment_status", "pending")
    
    @staticmethod
    def is_access_granted(request=None) -> bool:
        """Check if user has valid payment OR climber access for camera access"""
        # Check payment status
        payment_access = PaymentValidationService.check_payment_status() == "approved"
        
        # Check climber access if request provided
        climber_access = False
        if request:
            from core.services.climber_service import ClimberService
            climber_access = ClimberService.check_climber_access(request)
        
        return payment_access or climber_access
    
    @staticmethod
    def get_access_message(payment_status: str, camera_available: bool) -> str:
        """Generate user-friendly access message"""
        if payment_status != "approved":
            return "💳 Pagamento necessário para acessar câmera ao vivo"
        elif not camera_available:
            return "📷 Câmera temporariamente indisponível"
        else:
            return "✅ Acesso liberado - transmissão ao vivo disponível"
    
    @staticmethod
    def set_payment_status(status: str, timeout: int = 600):
        """Set payment status in cache"""
        cache.set("payment_status", status, timeout=timeout)


# Global service instances
camera_service = CameraStreamingService()
payment_service = PaymentValidationService()