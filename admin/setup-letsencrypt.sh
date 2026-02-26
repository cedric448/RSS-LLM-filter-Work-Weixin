#!/bin/bash
# 配置 Let's Encrypt SSL 证书

set -e

echo "=========================================="
echo "🔐 Let's Encrypt SSL 证书配置"
echo "=========================================="

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 请使用 root 权限运行${NC}"
    exit 1
fi

# 步骤1: 安装 Certbot
echo ""
echo "1️⃣  检查并安装 Certbot..."

if command -v certbot &> /dev/null; then
    echo -e "${GREEN}   ✓ Certbot 已安装${NC}"
else
    echo "   正在安装 Certbot..."
    
    # 根据不同系统安装
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL/TencentOS
        yum install -y certbot python3-certbot-nginx
    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}   ✗ 不支持的系统${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}   ✓ Certbot 安装完成${NC}"
fi

# 步骤2: 输入域名
echo ""
echo "2️⃣  配置域名..."
read -p "   请输入域名（例如: rss-admin.example.com）: " domain

if [ -z "$domain" ]; then
    echo -e "${RED}   ✗ 域名不能为空${NC}"
    exit 1
fi

read -p "   请输入邮箱地址（用于证书通知）: " email

if [ -z "$email" ]; then
    echo -e "${RED}   ✗ 邮箱不能为空${NC}"
    exit 1
fi

# 步骤3: 配置临时 Nginx
echo ""
echo "3️⃣  配置临时 Nginx（用于验证）..."

TEMP_NGINX_CONF="/etc/nginx/conf.d/rss-admin-temp.conf"

cat > "$TEMP_NGINX_CONF" << EOF
# 临时配置 - Let's Encrypt 验证用
server {
    listen 80;
    listen [::]:80;
    server_name $domain;
    
    root /var/www/certbot;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

mkdir -p /var/www/certbot
nginx -t && systemctl reload nginx
echo -e "${GREEN}   ✓ 临时配置已生效${NC}"

# 步骤4: 申请证书
echo ""
echo "4️⃣  申请 SSL 证书..."
echo -e "${YELLOW}   这可能需要几分钟...${NC}"

certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d "$domain" \
    --email "$email" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ 证书申请成功！${NC}"
    
    # 证书路径
    CERT_PATH="/etc/letsencrypt/live/$domain/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/$domain/privkey.pem"
    
    echo ""
    echo "   证书路径:"
    echo "   $CERT_PATH"
    echo "   $KEY_PATH"
else
    echo -e "${RED}   ✗ 证书申请失败${NC}"
    echo "   请检查:"
    echo "   1. 域名是否正确解析到本服务器"
    echo "   2. 80 端口是否可以访问"
    echo "   3. 防火墙是否正确配置"
    exit 1
fi

# 步骤5: 更新 Nginx 配置
echo ""
echo "5️⃣  更新 Nginx 配置..."

NGINX_CONF="/etc/nginx/conf.d/rss-admin.conf"

cat > "$NGINX_CONF" << EOF
# RSS Admin Backend - Nginx Configuration with Let's Encrypt
server {
    listen 80;
    listen [::]:80;
    server_name $domain;
    
    # Let's Encrypt 验证
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # 重定向到 HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $domain;
    
    # Let's Encrypt SSL 证书
    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate $CERT_PATH;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 访问日志
    access_log /var/log/nginx/rss-admin.access.log;
    error_log /var/log/nginx/rss-admin.error.log;
    
    # 反向代理
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 删除临时配置
rm -f "$TEMP_NGINX_CONF"

# 测试并重载 Nginx
if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}   ✓ Nginx 配置已更新${NC}"
else
    echo -e "${RED}   ✗ Nginx 配置错误${NC}"
    nginx -t
    exit 1
fi

# 步骤6: 配置自动续期
echo ""
echo "6️⃣  配置证书自动续期..."

# 添加 cron 任务（每天检查并续期）
CRON_JOB="0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'"

if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}   ✓ 自动续期任务已添加${NC}"
    echo "   每天凌晨 3 点自动检查证书"
else
    echo -e "${GREEN}   ✓ 自动续期任务已存在${NC}"
fi

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Let's Encrypt 配置完成！${NC}"
echo "=========================================="
echo ""
echo "📝 证书信息:"
echo "   域名: $domain"
echo "   证书路径: $CERT_PATH"
echo "   私钥路径: $KEY_PATH"
echo "   有效期: 90 天"
echo "   自动续期: 已配置（每天检查）"
echo ""
echo "🌐 访问地址:"
echo "   https://$domain"
echo ""
echo "🔧 管理命令:"
echo "   查看证书: certbot certificates"
echo "   手动续期: certbot renew"
echo "   测试续期: certbot renew --dry-run"
echo ""
