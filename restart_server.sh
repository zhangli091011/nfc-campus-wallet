#!/bin/bash
# 重启 NFC Campus Wallet 服务器

echo "正在重启 NFC Campus Wallet 服务器..."

# 重启 systemd 服务
sudo systemctl restart nfc-wallet

# 等待服务启动
sleep 2

# 检查服务状态
sudo systemctl status nfc-wallet --no-pager

echo ""
echo "服务器重启完成！"
