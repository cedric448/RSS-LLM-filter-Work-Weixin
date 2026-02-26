# 生产环境部署指南

## 🚀 快速部署

### 一键部署（推荐）

```bash
cd /root/project-wb/n8n/admin
sudo bash deploy.sh
```

部署脚本会自动完成：
- ✅ 环境检查
- ✅ 授权码配置
- ✅ 依赖安装
- ✅ Systemd 服务配置
- ✅ SSL 证书配置
- ✅ Nginx 反向代理配置
- ✅ 防火墙规则配置
- ✅ 服务启动

### SSL 证书选项

部署时会提示选择 SSL 证书类型：

1. **使用现有证书**：如果已有证书，选择此项
2. **生成自签名证书**：测试环境使用
3. **跳过配置**：稍后手动配置

### Let's Encrypt 证书（推荐生产环境）

如果有域名，推荐使用 Let's Encrypt 免费证书：

```bash
cd /root/project-wb/n8n/admin
sudo bash setup-letsencrypt.sh
```

**前提条件**：
- 域名已解析到服务器 IP
- 80 端口可以外网访问
- 域名处于有效状态

## 📋 手动部署步骤

### 1. 配置授权码

```bash
cd /root/project-wb/n8n/admin

# 生成强密码
openssl rand -base64 32 > .auth_code

# 创建配置文件
cat > .env << EOF
RSS_ADMIN_AUTH_CODE=$(cat .auth_code)
FLASK_ENV=production
EOF

# 保存授权码
cat .auth_code
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 配置 Systemd 服务

```bash
# 创建日志目录
mkdir -p /var/log/rss-admin

# 创建服务文件
sudo tee /etc/systemd/system/rss-admin.service > /dev/null << EOF
[Unit]
Description=RSS Admin Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/project-wb/n8n/admin
Environment="RSS_ADMIN_AUTH_CODE=your-auth-code-here"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 /root/project-wb/n8n/admin/app.py
Restart=always
RestartSec=10

StandardOutput=append:/var/log/rss-admin/access.log
StandardError=append:/var/log/rss-admin/error.log

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable rss-admin
sudo systemctl start rss-admin

# 检查状态
sudo systemctl status rss-admin
```

### 4. 配置 SSL 证书

#### 方法A：使用 Let's Encrypt

```bash
# 安装 Certbot
sudo yum install -y certbot python3-certbot-nginx  # CentOS/RHEL
# 或
sudo apt-get install -y certbot python3-certbot-nginx  # Debian/Ubuntu

# 申请证书
sudo certbot certonly --nginx -d yourdomain.com

# 证书路径
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### 方法B：自签名证书

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/rss-admin.key \
    -out /etc/nginx/ssl/rss-admin.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=RSS-Admin/CN=localhost"
```

### 5. 配置 Nginx

```bash
# 创建配置文件
sudo tee /etc/nginx/conf.d/rss-admin.conf > /dev/null << 'EOF'
# HTTP 重定向
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com;  # 修改为你的域名
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;  # 修改为你的域名
    
    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 反向代理
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 6. 配置防火墙

#### Firewalld（CentOS/RHEL）

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### UFW（Ubuntu/Debian）

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

#### 云服务器安全组

如果使用云服务器，还需要在控制台配置安全组：
- 开放 80 端口（HTTP）
- 开放 443 端口（HTTPS）

## 🔒 安全加固

### 1. IP 白名单（可选）

编辑 Nginx 配置，添加 IP 限制：

```nginx
server {
    listen 443 ssl http2;
    
    # IP 白名单
    allow 192.168.1.0/24;  # 允许内网
    allow YOUR_IP_ADDRESS;  # 允许特定 IP
    deny all;               # 拒绝其他所有
    
    location / {
        proxy_pass http://127.0.0.1:5002;
    }
}
```

### 2. 限流配置

防止暴力破解：

```nginx
http {
    # 限流配置
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    
    server {
        location /login {
            limit_req zone=login_limit burst=2;
            proxy_pass http://127.0.0.1:5002;
        }
    }
}
```

### 3. 修改默认授权码

```bash
# 生成新密码
NEW_PASSWORD=$(openssl rand -base64 32)

# 更新配置
echo "RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD" > /root/project-wb/n8n/admin/.env

# 更新 Systemd 服务
sudo sed -i "s/Environment=\"RSS_ADMIN_AUTH_CODE=.*/Environment=\"RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD\"/" /etc/systemd/system/rss-admin.service

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart rss-admin

# 保存新密码
echo "新授权码: $NEW_PASSWORD"
```

## 🔧 运维管理

### 服务管理

```bash
# 启动服务
sudo systemctl start rss-admin

# 停止服务
sudo systemctl stop rss-admin

# 重启服务
sudo systemctl restart rss-admin

# 查看状态
sudo systemctl status rss-admin

# 查看日志
sudo journalctl -u rss-admin -f
```

### 日志管理

```bash
# 应用日志
tail -f /var/log/rss-admin/access.log
tail -f /var/log/rss-admin/error.log

# Nginx 日志
tail -f /var/log/nginx/rss-admin.access.log
tail -f /var/log/nginx/rss-admin.error.log

# 清理旧日志
sudo find /var/log/rss-admin -name "*.log" -mtime +30 -delete
```

### 证书续期

Let's Encrypt 证书每 90 天过期，需要续期：

```bash
# 手动续期
sudo certbot renew

# 测试续期（不实际执行）
sudo certbot renew --dry-run

# 自动续期已配置在 crontab
crontab -l | grep certbot
```

### 监控检查

```bash
# 检查服务状态
systemctl is-active rss-admin

# 检查端口监听
netstat -tuln | grep :5002

# 测试 HTTPS 连接
curl -k https://localhost:443/health

# 检查 SSL 证书有效期
openssl x509 -in /etc/nginx/ssl/rss-admin.crt -noout -dates
```

## 📊 性能优化

### 1. Gunicorn 部署（推荐生产环境）

安装 Gunicorn：

```bash
pip3 install gunicorn
```

修改 Systemd 服务：

```ini
[Service]
ExecStart=/usr/bin/python3 -m gunicorn \
    --bind 127.0.0.1:5002 \
    --workers 4 \
    --threads 2 \
    --timeout 60 \
    --access-logfile /var/log/rss-admin/access.log \
    --error-logfile /var/log/rss-admin/error.log \
    app:app
```

### 2. Nginx 缓存

```nginx
http {
    # 缓存配置
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=rss_cache:10m max_size=100m;
    
    server {
        location /api/sources {
            proxy_cache rss_cache;
            proxy_cache_valid 200 5m;
            proxy_pass http://127.0.0.1:5002;
        }
    }
}
```

## 🆘 故障排查

### 问题：服务无法启动

```bash
# 查看详细日志
journalctl -u rss-admin -n 50 --no-pager

# 检查端口占用
lsof -ti:5002

# 检查配置文件
cat /root/project-wb/n8n/admin/.env
```

### 问题：Nginx 配置错误

```bash
# 测试配置
nginx -t

# 查看错误日志
tail -50 /var/log/nginx/error.log
```

### 问题：SSL 证书错误

```bash
# 检查证书文件
ls -la /etc/nginx/ssl/
ls -la /etc/letsencrypt/live/

# 测试证书
openssl s_client -connect localhost:443 -servername yourdomain.com
```

### 问题：无法访问

1. 检查防火墙
2. 检查云服务器安全组
3. 检查域名解析
4. 检查服务状态

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [SECURITY.md](SECURITY.md) - 安全配置
- [QUICKSTART.md](QUICKSTART.md) - 快速开始

## 💡 最佳实践

1. ✅ 使用强随机密码
2. ✅ 配置 HTTPS（生产环境必须）
3. ✅ 定期更换授权码
4. ✅ 配置 IP 白名单（如果可能）
5. ✅ 启用访问日志监控
6. ✅ 定期备份配置文件
7. ✅ 设置证书自动续期
8. ✅ 使用 Gunicorn 多进程部署
