"""
Django Management Command: Stop Camera Streaming
Provides CLI interface for stopping camera streaming service
"""
from django.core.management.base import BaseCommand, CommandError
from streaming.services import camera_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Stop camera streaming service'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force stop (kill process)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("⏹️ Stopping Camera Streaming Service...")
        
        # Check if running
        if not camera_service.is_streaming:
            self.stdout.write(
                self.style.WARNING("⚠️ No streaming service running")
            )
            return
        
        # Stop streaming
        try:
            if options['force']:
                self.stdout.write("🔥 Force stopping streaming...")
                if camera_service.ffmpeg_process:
                    camera_service.ffmpeg_process.kill()
                    camera_service.ffmpeg_process.wait()
                camera_service.is_streaming = False
                camera_service.ffmpeg_process = None
            else:
                success = camera_service.stop_streaming()
                if not success:
                    raise CommandError("Failed to stop streaming gracefully")
            
            self.stdout.write(
                self.style.SUCCESS("✅ Camera streaming stopped successfully")
            )
            
        except Exception as e:
            raise CommandError(f"Error stopping streaming: {e}")