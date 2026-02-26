#!/bin/bash
# RSS 管理后台 - 生产环境部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 RSS 管理后台 - 生产环境部署"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 错误: 请使用 root 权限运行此脚本${NC}"
    echo "   sudo bash deploy.sh"
    exit 1
fi

# 配置变量
PROJECT_DIR="/root/project-wb/n8n/admin"
SERVICE_FILE="/etc/systemd/system/rss-admin.service"
NGINX_CONF="/etc/nginx/conf.d/rss-admin.conf"
LOG_DIR="/var/log/rss-admin"
SSL_DIR="/etc/nginx/ssl"

echo ""
echo "📋 部署配置:"
echo "   项目目录: $PROJECT_DIR"
echo "   服务文件: $SERVICE_FILE"
echo "   Nginx 配置: $NGINX_CONF"
echo "   日志目录: $LOG_DIR"
echo "   SSL 目录: $SSL_DIR"
echo ""

# 步骤1: 检查环境
echo "1️⃣  检查部署环境..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}   ✗ 未安装 Python3${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Python3: $(python3 --version)${NC}"

# 检查 Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}   ✗ 未安装 Nginx${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Nginx: $(nginx -v 2>&1)${NC}"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}   ✗ 项目目录不存在: $PROJECT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ 项目目录存在${NC}"

# 步骤2: 配置授权码
echo ""
echo "2️⃣  配置授权码..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}   ⚠️  .env 文件不存在，正在创建...${NC}"
    
    # 生成随机授权码
    NEW_AUTH_CODE=$(openssl rand -base64 32)
    
    cat > "$PROJECT_DIR/.env" << EOF
# RSS 管理后台生产环境配置
RSS_ADMIN_AUTH_CODE=$NEW_AUTH_CODE
FLASK_ENV=production
EOF
    
    echo -e "${GREEN}   ✓ 已生成新的授权码${NC}"
    echo -e "${YELLOW}   📝 授权码: $NEW_AUTH_CODE${NC}"
    echo -e "${YELLOW}   💾 请保存此授权码，用于登录后台！${NC}"
    echo ""
    read -p "   按 Enter 继续部署..."
else
    echo -e "${GREEN}   ✓ 使用现有 .env 配置${NC}"
    AUTH_CODE=$(grep RSS_ADMIN_AUTH_CODE "$PROJECT_DIR/.env" | cut -d '=' -f2)
    if [ -n "$AUTH_CODE" ]; then
        echo -e "${GREEN}   授权码: ${AUTH_CODE:0:5}...${AUTH_CODE: -5}${NC}"
    fi
fi

# 步骤3: 安装依赖
echo ""
echo "3️⃣  安装 Python 依赖..."
cd "$PROJECT_DIR"
pip3 install -q -r requirements.txt
echo -e "${GREEN}   ✓ 依赖安装完成${NC}"

# 步骤4: 创建日志目录
echo ""
echo "4️⃣  创建日志目录..."
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
echo -e "${GREEN}   ✓ 日志目录: $LOG_DIR${NC}"

# 步骤5: 配置 Systemd 服务
echo ""
echo "5️⃣  配置 Systemd 服务..."

# 读取授权码
AUTH_CODE=$(grep RSS_ADMIN_AUTH_CODE "$PROJECT_DIR/.env" | cut -d '=' -f2)

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=RSS Admin Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="RSS_ADMIN_AUTH_CODE=$AUTH_CODE"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 $PROJECT_DIR/app.py
Restart=always
RestartSec=10

# 日志
StandardOutput=append:$LOG_DIR/access.log
StandardError=append:$LOG_DIR/error.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}   ✓ 服务配置文件已创建${NC}"

# 重载 systemd 并启动服务
systemctl daemon-reload
systemctl enable rss-admin.service
systemctl restart rss-admin.service

sleep 2

if systemctl is-active --quiet rss-admin.service; then
    echo -e "${GREEN}   ✓ 服务启动成功${NC}"
else
    echo -e "${RED}   ✗ 服务启动失败${NC}"
    echo "   查看日志: journalctl -u rss-admin.service -n 50"
    exit 1
fi

# 步骤6: 配置 SSL 证书
echo ""
echo "6️⃣  配置 SSL 证书..."
echo ""
echo "   请选择 SSL 证书类型:"
echo "   1) 使用现有证书（手动配置）"
echo "   2) 生成自签名证书（测试用）"
echo "   3) 跳过（稍后配置）"
echo ""
read -p "   请输入选择 [1-3]: " ssl_choice

mkdir -p "$SSL_DIR"

case $ssl_choice in
    1)
        echo ""
        echo -e "${YELLOW}   请手动将证书文件复制到:${NC}"
        echo "   证书: $SSL_DIR/rss-admin.crt"
        echo "   私钥: $SSL_DIR/rss-admin.key"
        echo ""
        read -p "   完成后按 Enter 继续..."
        
        if [ ! -f "$SSL_DIR/rss-admin.crt" ] || [ ! -f "$SSL_DIR/rss-admin.key" ]; then
            echo -e "${RED}   ✗ 证书文件不存在${NC}"
            exit 1
        fi
        echo -e "${GREEN}   ✓ 证书文件已就位${NC}"
        ;;
    2)
        echo "   正在生成自签名证书..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/rss-admin.key" \
            -out "$SSL_DIR/rss-admin.crt" \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=RSS-Admin/CN=localhost"
        
        chmod 600 "$SSL_DIR/rss-admin.key"
        chmod 644 "$SSL_DIR/rss-admin.crt"
        echo -e "${GREEN}   ✓ 自签名证书已生成${NC}"
        echo -e "${YELLOW}   ⚠️  自签名证书仅供测试，生产环境请使用正式证书${NC}"
        ;;
    3)
        echo -e "${YELLOW}   ⊗ 跳过 SSL 配置${NC}"
        echo "   稍后可手动配置证书"
        ;;
    *)
        echo -e "${RED}   ✗ 无效选择${NC}"
        exit 1
        ;;
esac

# 步骤7: 配置 Nginx
echo ""
echo "7️⃣  配置 Nginx..."

# 询问域名
read -p "   请输入域名（留空使用 IP 访问）: " domain_name

if [ -z "$domain_name" ]; then
    domain_name="_"  # Nginx 默认 server
fi

# 生成 Nginx 配置
cat > "$NGINX_CONF" << EOF
# RSS Admin Backend - Nginx Configuration
# Generated at $(date)

# HTTP 配置
server {
    listen 80;
    listen [::]:80;
    server_name $domain_name;
    
    # Let's Encrypt 验证目录
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # 重定向到 HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $domain_name;
    
    # SSL 证书配置
    ssl_certificate $SSL_DIR/rss-admin.crt;
    ssl_certificate_key $SSL_DIR/rss-admin.key;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 访问日志
    access_log /var/log/nginx/rss-admin.access.log;
    error_log /var/log/nginx/rss-admin.error.log;
    
    # 反向代理到 Flask 应用
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo -e "${GREEN}   ✓ Nginx 配置已创建${NC}"

# 测试 Nginx 配置
echo "   测试 Nginx 配置..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}   ✓ Nginx 配置测试通过${NC}"
    
    # 重载 Nginx
    systemctl reload nginx
    echo -e "${GREEN}   ✓ Nginx 已重载${NC}"
else
    echo -e "${RED}   ✗ Nginx 配置测试失败${NC}"
    nginx -t
    exit 1
fi

# 步骤8: 配置防火墙（可选）
echo ""
echo "8️⃣  配置防火墙..."
echo "   是否配置防火墙规则？[y/N]"
read -p "   " configure_firewall

if [ "$configure_firewall" = "y" ] || [ "$configure_firewall" = "Y" ]; then
    # 检查防火墙工具
    if command -v firewall-cmd &> /dev/null; then
        echo "   使用 firewalld..."
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        echo -e "${GREEN}   ✓ 防火墙规则已添加（firewalld）${NC}"
    elif command -v ufw &> /dev/null; then
        echo "   使用 ufw..."
        ufw allow 80/tcp
        ufw allow 443/tcp
        echo -e "${GREEN}   ✓ 防火墙规则已添加（ufw）${NC}"
    else
        echo -e "${YELLOW}   ⚠️  未检测到防火墙工具${NC}"
    fi
else
    echo -e "${YELLOW}   ⊗ 跳过防火墙配置${NC}"
fi

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo ""
echo "📝 部署信息:"
echo "   服务状态: systemctl status rss-admin"
echo "   服务日志: journalctl -u rss-admin -f"
echo "   应用日志: tail -f $LOG_DIR/access.log"
echo "   Nginx 日志: tail -f /var/log/nginx/rss-admin.access.log"
echo ""
echo "🌐 访问地址:"
if [ "$domain_name" = "_" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "   HTTP:  http://$SERVER_IP"
    echo "   HTTPS: https://$SERVER_IP"
else
    echo "   HTTP:  http://$domain_name"
    echo "   HTTPS: https://$domain_name"
fi
echo ""
echo "🔐 授权码:"
AUTH_CODE=$(grep RSS_ADMIN_AUTH_CODE "$PROJECT_DIR/.env" | cut -d '=' -f2)
echo "   $AUTH_CODE"
echo ""
echo "🔧 管理命令:"
echo "   启动服务: systemctl start rss-admin"
echo "   停止服务: systemctl stop rss-admin"
echo "   重启服务: systemctl restart rss-admin"
echo "   查看状态: systemctl status rss-admin"
echo "   重载 Nginx: systemctl reload nginx"
echo ""

# 测试服务
echo "🧪 测试服务连接..."
sleep 1
if curl -k -s https://localhost:443 > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ HTTPS 服务正常${NC}"
elif curl -s http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ HTTP 服务正常${NC}"
else
    echo -e "${YELLOW}   ⚠️  服务可能需要几秒钟启动${NC}"
fi

echo ""
echo "=========================================="
