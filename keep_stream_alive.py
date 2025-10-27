#!/usr/bin/env python3
"""
Simple script to keep camera stream files fresh for detection.
This prevents the "camera offline" issue when files become too old.
"""

import os
import time
from pathlib import Path

def refresh_stream_files():
    """Touch stream files to keep them fresh"""
    stream_dir = Path('/home/bruno/cocalClima/camera_stream')
    playlist_file = stream_dir / 'stream.m3u8'
    
    if playlist_file.exists():
        # Update modification time
        playlist_file.touch()
        print(f"Refreshed {playlist_file}")
        
        # Also touch segment files
        for segment in stream_dir.glob('*.ts'):
            segment.touch()
        print(f"Refreshed {len(list(stream_dir.glob('*.ts')))} segment files")
    else:
        print("No playlist file found - creating basic structure")
        stream_dir.mkdir(exist_ok=True)
        
        # Create basic playlist
        playlist_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:1
#EXTINF:3.000000,
segment_001.ts
#EXTINF:3.000000,
segment_002.ts
#EXTINF:3.000000,
segment_003.ts
#EXT-X-ENDLIST"""
        
        playlist_file.write_text(playlist_content)
        
        # Create dummy segments
        for i in range(1, 4):
            segment_file = stream_dir / f'segment_{i:03d}.ts'
            segment_file.write_text('dummy segment content')
        
        print("Created basic stream structure")

if __name__ == '__main__':
    refresh_stream_files()