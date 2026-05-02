#!/bin/bash
# Deploy database initialization fix to production server

echo "Deploying database initialization fix..."

# Copy the fixed app/main.py to the server
scp app/main.py ubuntu@your-server:/home/ubuntu/nfc-campus-wallet/app/main.py

# Restart the service
ssh ubuntu@your-server "sudo systemctl restart nfc-wallet"

echo "Deployment complete. Checking service status..."
ssh ubuntu@your-server "sudo systemctl status nfc-wallet"
