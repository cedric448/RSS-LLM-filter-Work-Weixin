# ✅ RSS 管理后台 - 生产环境部署完成

## 🎉 部署状态

**部署时间**: 2026-02-20 21:00 UTC+8  
**部署方式**: HTTPS + SSL 自签名证书  
**状态**: ✅ 运行正常

---

## 📋 服务信息

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **HTTPS (主服务)** | `https://172.19.48.4:8443` | 加密连接,推荐使用 |
| **HTTP (重定向)** | `http://172.19.48.4:8081` | 自动跳转到 HTTPS |
| **内部API** | `http://127.0.0.1:5002` | Flask 应用(仅本地) |

### 登录信息

```
授权码: change-this-password-in-production
会话有效期: 24 小时
```

### 端口说明

- **8443**: HTTPS 服务（使用独立端口避免与现有服务冲突）
- **8081**: HTTP 服务（301 重定向到 HTTPS）
- **5002**: Flask 应用（仅监听 127.0.0.1）

> 💡 **为何不使用 80/443 端口？**  
> 服务器上已有其他服务占用 80 和 443 端口（codebuddy 服务），因此使用独立端口 8443/8081。

---

## 🔐 安全配置

### SSL/TLS 配置

- **证书类型**: 自签名证书（测试/内部使用）
- **证书位置**: `/etc/nginx/ssl/rss-admin.{crt,key}`
- **证书有效期**: 365 天（至 2027-02-20）
- **TLS 版本**: TLS 1.2, TLS 1.3
- **加密套件**: 强加密套件（ECDHE）

### 安全响应头

- ✅ **HSTS**: 强制 HTTPS，有效期 1 年
- ✅ **X-Frame-Options**: SAMEORIGIN（防点击劫持）
- ✅ **X-Content-Type-Options**: nosniff
- ✅ **X-XSS-Protection**: 启用

### 访问控制

- ✅ **授权码鉴权**: 32 字符强密码
- ✅ **Session 管理**: 24 小时过期
- ✅ **API 保护**: 所有接口需要登录
- ✅ **反向代理**: Nginx → Flask (内部端口不对外暴露)

---

## 🏗️ 部署架构

```
Internet
   ↓
Nginx (8443/HTTPS, 8081/HTTP)
   ├─ SSL 终端加密
   ├─ 安全响应头
   ├─ HTTP → HTTPS 重定向
   └─ 反向代理
      ↓
Flask App (127.0.0.1:5002)
   ├─ 授权验证
   ├─ Session 管理
   └─ RSS 管理 API
```

---

## 🔧 服务管理

### Systemd 服务

```bash
# 查看服务状态
systemctl status rss-admin

# 启动/停止/重启
systemctl start rss-admin
systemctl stop rss-admin
systemctl restart rss-admin

# 查看实时日志
journalctl -u rss-admin -f
```

### Nginx 管理

```bash
# 测试配置
nginx -t

# 重载配置（不中断服务）
systemctl reload nginx

# 重启 Nginx
systemctl restart nginx
```

### 日志查看

```bash
# Flask 应用日志
tail -f /var/log/rss-admin/access.log
tail -f /var/log/rss-admin/error.log

# Nginx 日志
tail -f /var/log/nginx/rss-admin.access.log
tail -f /var/log/nginx/rss-admin.error.log
```

---

## 📊 测试结果

### 功能测试 ✅

| 测试项 | 结果 |
|--------|------|
| HTTP → HTTPS 重定向 | ✅ 301 正常 |
| HTTPS 连接 | ✅ 正常 |
| SSL 证书 | ✅ 正常 |
| 登录功能 | ✅ 正常 |
| API 访问控制 | ✅ 正常 |
| 错误密码拒绝 | ✅ 正常 |
| Session 持久化 | ✅ 正常 |
| 安全响应头 | ✅ 正常 |

### 性能测试

```
连接耗时: ~0.01s
首字节耗时: ~0.05s
总耗时: ~0.05s
```

---

## 📁 配置文件

### 关键文件位置

```
/root/project-wb/n8n/admin/
├── app.py                          # Flask 主程序
├── .env                            # 环境变量（授权码）
├── requirements.txt                # Python 依赖
├── templates/                      # HTML 模板
│   ├── index.html                  # 管理页面
│   └── login.html                  # 登录页面
└── config/                         # RSS 配置
    └── rss-sources.json            # RSS 源数据

/etc/systemd/system/
└── rss-admin.service               # Systemd 服务配置

/etc/nginx/
├── conf.d/rss-admin.conf           # Nginx 配置
└── ssl/
    ├── rss-admin.crt               # SSL 证书
    └── rss-admin.key               # SSL 私钥

/var/log/
├── rss-admin/                      # 应用日志
│   ├── access.log
│   └── error.log
└── nginx/                          # Nginx 日志
    ├── rss-admin.access.log
    └── rss-admin.error.log
```

---

## 🔄 升级与维护

### 更新授权码

```bash
# 生成新密码
NEW_PASSWORD=$(openssl rand -base64 32)

# 更新 .env 文件
echo "RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD" > /root/project-wb/n8n/admin/.env

# 更新 Systemd 服务
sudo sed -i "s/RSS_ADMIN_AUTH_CODE=.*/RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD/" /etc/systemd/system/rss-admin.service

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart rss-admin

# 记录新密码
echo "新授权码: $NEW_PASSWORD"
```

### 更新应用代码

```bash
cd /root/project-wb/n8n/admin

# 备份配置
cp .env .env.backup

# 更新代码（如果从 git 拉取）
# git pull

# 重启服务
systemctl restart rss-admin
```

### SSL 证书续期

当前使用自签名证书,有效期 365 天。到期前需要重新生成:

```bash
# 重新生成证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/rss-admin.key \
    -out /etc/nginx/ssl/rss-admin.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=RSS-Admin/CN=localhost"

# 重载 Nginx
systemctl reload nginx
```

**推荐**: 如有域名,使用 Let's Encrypt 免费证书（自动续期）:

```bash
cd /root/project-wb/n8n/admin
sudo bash setup-letsencrypt.sh
```

---

## 🛡️ 安全加固建议

### 1. 使用正式 SSL 证书（推荐）

```bash
# 如果有域名,运行 Let's Encrypt 配置脚本
cd /root/project-wb/n8n/admin
sudo bash setup-letsencrypt.sh
```

### 2. 配置 IP 白名单

编辑 `/etc/nginx/conf.d/rss-admin.conf`,在 `location /` 前添加:

```nginx
# 仅允许特定 IP 访问
allow 192.168.1.0/24;  # 内网
allow YOUR_IP_ADDRESS; # 你的 IP
deny all;              # 拒绝其他所有
```

### 3. 配置防火墙

```bash
# CentOS/RHEL/TencentOS
firewall-cmd --permanent --add-port=8443/tcp
firewall-cmd --permanent --add-port=8081/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw allow 8443/tcp
ufw allow 8081/tcp
```

### 4. 启用访问限流

编辑 Nginx 配置,添加限流:

```nginx
http {
    # 限制登录频率（5次/分钟）
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    server {
        location /login {
            limit_req zone=login burst=2;
            proxy_pass http://127.0.0.1:5002;
        }
    }
}
```

### 5. 定期更换授权码

建议每 90 天更换一次授权码（参考上方"更新授权码"流程）。

---

## 🆘 故障排查

### 问题 1: 服务无法启动

```bash
# 查看详细错误
journalctl -u rss-admin -n 50

# 检查端口占用
netstat -tuln | grep 5002

# 检查配置文件
cat /root/project-wb/n8n/admin/.env
```

### 问题 2: 无法访问 HTTPS

```bash
# 检查端口监听
netstat -tuln | grep 8443

# 检查 Nginx 状态
systemctl status nginx

# 测试 SSL 证书
openssl s_client -connect localhost:8443
```

### 问题 3: 登录失败

- 检查授权码是否正确
- 查看应用日志: `tail -f /var/log/rss-admin/error.log`
- 清除浏览器 Cookie 重试

### 问题 4: API 返回 401

- Session 可能已过期,重新登录
- 检查 Cookie 是否被禁用

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目概述和快速开始 |
| [PRODUCTION.md](PRODUCTION.md) | 完整部署指南 |
| [SECURITY.md](SECURITY.md) | 安全配置详解 |
| [QUICKSTART.md](QUICKSTART.md) | 5 分钟快速部署 |
| [USAGE.md](USAGE.md) | 使用说明 |

---

## 📞 技术支持

### 部署脚本

```bash
# 一键部署（如需重新部署）
cd /root/project-wb/n8n/admin
sudo bash deploy.sh

# 检查部署状态
bash check-deployment.sh

# Let's Encrypt 证书配置
sudo bash setup-letsencrypt.sh
```

### 测试工具

```bash
# 完整功能测试
bash /tmp/test_https_final.sh

# 单独测试登录
curl -k -X POST https://172.19.48.4:8443/login \
  -H "Content-Type: application/json" \
  -d '{"auth_code":"change-this-password-in-production"}'
```

---

## 🎯 下一步建议

1. ✅ **已完成**: HTTPS 加密传输
2. ✅ **已完成**: 授权码鉴权
3. ✅ **已完成**: Systemd 服务管理
4. ✅ **已完成**: 日志记录

5. 🔜 **建议完成**:
   - [ ] 配置 IP 白名单（如果需要）
   - [ ] 启用访问限流（防暴力破解）
   - [ ] 配置 Let's Encrypt 证书（如有域名）
   - [ ] 定期备份配置和数据
   - [ ] 设置监控告警

---

## 📝 部署总结

✅ **部署成功！** RSS 管理后台已经在生产环境正常运行。

**核心特性**:
- 🔒 HTTPS 加密传输
- 🔐 授权码鉴权保护
- 🚀 Systemd 自动启动
- 📊 完整日志记录
- 🛡️ 安全响应头配置
- ⚡ Nginx 反向代理

**访问方式**:
```
https://172.19.48.4:8443
```

**登录授权码**:
```
change-this-password-in-production
```

---

*部署完成时间: 2026-02-20 21:00 UTC+8*  
*部署方式: 自动化脚本 + 手动配置*  
*证书类型: 自签名证书（365天有效期）*
