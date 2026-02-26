# 快速开始指南

## 🚀 5 分钟快速部署

### 1. 配置授权码（必须）

```bash
cd /root/project-wb/n8n/admin

# 生成强密码
openssl rand -base64 32

# 创建配置文件
cat > .env << EOF
RSS_ADMIN_AUTH_CODE=$(openssl rand -base64 32)
EOF

# 查看生成的密码
cat .env
```

**保存这个密码！** 你将用它登录后台。

### 2. 安装并启动

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务
./start.sh
```

### 3. 访问后台

1. 浏览器打开: http://localhost:5002
2. 输入步骤 1 中生成的授权码
3. 开始管理 RSS 订阅源

## 📝 常用操作

### 添加 RSS 源

1. 点击 **"➕ 添加 RSS 源"**
2. 填写信息：
   - 公众号名称: `机器之心`
   - RSS 链接: `http://rss.jintiankansha.me/rss/YOUR_CODE`
   - 描述: `AI 行业资讯`（可选）
3. 点击 **"保存"**

### 修改授权码

```bash
# 生成新密码
NEW_PASSWORD=$(openssl rand -base64 32)

# 更新配置
echo "RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD" > .env

# 重启服务
./start.sh

# 新密码
echo $NEW_PASSWORD
```

### 查看当前配置

```bash
# 查看授权码（脱敏显示）
grep RSS_ADMIN_AUTH_CODE .env | sed 's/\(.\{5\}\).*\(.\{5\}\)/\1...\2/'

# 查看 RSS 源配置
cat ../config/rss-sources.json | python3 -m json.tool
```

### 停止服务

```bash
# Ctrl+C 停止前台运行

# 或查找并杀死进程
ps aux | grep "python3 app.py"
kill -9 <PID>
```

## 🔧 故障排查

### 问题：端口被占用

```bash
# 查找占用 5002 端口的进程
lsof -ti:5002

# 杀死进程
lsof -ti:5002 | xargs kill -9

# 或修改端口（编辑 app.py 最后一行）
```

### 问题：忘记授权码

```bash
# 查看当前配置的授权码
cat .env | grep RSS_ADMIN_AUTH_CODE

# 或重新生成
openssl rand -base64 32 > .env
```

### 问题：登录后提示未授权

```bash
# 清除浏览器 Cookie
# 或使用无痕模式重新登录
```

### 问题：配置保存失败

```bash
# 检查配置目录权限
ls -la ../config/

# 创建配置目录
mkdir -p ../config/

# 赋予写入权限
chmod 755 ../config/
```

## 📦 Docker 快速部署

### 构建镜像

```bash
cd /root/project-wb/n8n/admin
docker build -t rss-admin .
```

### 运行容器

```bash
docker run -d \
  --name rss-admin \
  -p 5002:5002 \
  -v $(pwd)/../config:/app/config \
  -e RSS_ADMIN_AUTH_CODE="your-password-here" \
  rss-admin
```

### 查看日志

```bash
docker logs -f rss-admin
```

## 🌐 生产环境部署

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name rss-admin.your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name rss-admin.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 限制访问来源（可选）
    allow 192.168.1.0/24;  # 内网
    deny all;
    
    location / {
        proxy_pass http://localhost:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 使用 Systemd 服务

创建 `/etc/systemd/system/rss-admin.service`:

```ini
[Unit]
Description=RSS Admin Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/project-wb/n8n/admin
Environment="RSS_ADMIN_AUTH_CODE=your-password-here"
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
systemctl daemon-reload
systemctl enable rss-admin
systemctl start rss-admin
systemctl status rss-admin
```

## 📚 下一步

- 阅读 [USAGE.md](USAGE.md) 了解详细使用方法
- 阅读 [SECURITY.md](SECURITY.md) 了解安全配置
- 阅读 [README.md](README.md) 了解完整功能

## 💡 提示

- 💾 **定期备份**: 备份 `../config/rss-sources.json`
- 🔑 **安全密码**: 使用强随机密码
- 🔄 **定期更换**: 每 3-6 个月更换授权码
- 📝 **记录密码**: 将授权码保存到密码管理器
- 🔒 **限制访问**: 生产环境配置防火墙规则

## 🆘 获取帮助

- 查看日志: `docker compose logs rss-admin`
- 运行测试: `python3 test_api.py`
- 检查配置: `cat .env`
- 测试连接: `curl http://localhost:5002/health`
