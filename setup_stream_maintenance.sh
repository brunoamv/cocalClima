#!/bin/bash
# Setup automatic stream file maintenance

echo "Setting up stream maintenance cron job..."

# Add cron job to refresh stream files every 10 minutes
(crontab -l 2>/dev/null; echo "*/10 * * * * /usr/bin/python3 /home/bruno/cocalClima/keep_stream_alive.py >/dev/null 2>&1") | crontab -

echo "Cron job added successfully!"
echo "Stream files will be refreshed every 10 minutes to prevent 'camera offline' issues."

# Show current crontab
echo ""
echo "Current crontab:"
crontab -l