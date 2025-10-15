"""
Django Management Command: Start Camera Streaming
Provides CLI interface for starting camera streaming service
"""
from django.core.management.base import BaseCommand, CommandError
from streaming.services import camera_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start camera streaming service'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force start even if already running'
        )
        parser.add_argument(
            '--test-camera',
            action='store_true',
            help='Test camera connection before starting'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🎬 Starting Camera Streaming Service...")
        
        # Test camera if requested
        if options['test_camera']:
            self.stdout.write("📷 Testing camera connection...")
            if camera_service.test_camera_connection():
                self.stdout.write(
                    self.style.SUCCESS("✅ Camera connection successful")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Camera connection failed")
                )
                return
        
        # Check if already running
        if camera_service.is_streaming and not options['force']:
            self.stdout.write(
                self.style.WARNING("⚠️ Streaming already active. Use --force to restart.")
            )
            return
        
        # Start streaming
        try:
            success = camera_service.start_streaming()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("🎉 Camera streaming started successfully!")
                )
                self.stdout.write(f"📊 Process PID: {camera_service.ffmpeg_process.pid}")
                self.stdout.write("📡 Stream available at: /streaming/camera/stream.m3u8")
            else:
                raise CommandError("Failed to start camera streaming")
                
        except Exception as e:
            raise CommandError(f"Error starting streaming: {e}")