# 安全配置指南

## 🔐 鉴权机制

本系统使用基于 **AUTH_CODE** 的登录认证机制，确保只有授权用户才能访问后台管理功能。

### 工作原理

1. **授权码验证**: 用户输入授权码进行登录
2. **Session 管理**: 登录成功后创建 Session（有效期 24 小时）
3. **中间件拦截**: 所有 API 请求都经过鉴权中间件验证
4. **自动跳转**: 未登录用户自动跳转到登录页

### 安全特性

✅ **强制登录**: 所有管理功能都需要登录  
✅ **Session 持久化**: 登录后 24 小时内无需重新输入密码  
✅ **自动过期**: Session 超时后自动失效  
✅ **安全退出**: 提供退出登录功能，清除 Session  
✅ **API 保护**: 未授权 API 请求返回 401 错误  

## 🔑 授权码配置

### 方法一：环境变量文件（推荐）

1. 复制配置文件模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件：
```bash
RSS_ADMIN_AUTH_CODE=your-strong-password-here
```

3. 重启服务使配置生效

### 方法二：系统环境变量

```bash
# Linux/Mac
export RSS_ADMIN_AUTH_CODE="your-strong-password-here"

# 永久设置
echo 'export RSS_ADMIN_AUTH_CODE="your-password"' >> ~/.bashrc
source ~/.bashrc
```

### 方法三：Docker 环境变量

```yaml
services:
  rss-admin:
    environment:
      - RSS_ADMIN_AUTH_CODE=your-strong-password-here
```

## 🛡️ 密码强度建议

### 推荐做法

✅ **长度**: 至少 20 个字符  
✅ **复杂性**: 包含大小写字母、数字、特殊字符  
✅ **随机性**: 使用随机生成器生成  
✅ **唯一性**: 不要重复使用其他服务的密码  
✅ **保密性**: 不要在代码中硬编码，不要提交到 Git  

### 生成强密码

```bash
# 使用 OpenSSL（推荐）
openssl rand -base64 32

# 输出示例: eID6g1ka71A-p7UVNgwpBRnIIjXiOvPp

# 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 使用 pwgen
pwgen -s 32 1
```

### 避免使用

❌ 常见密码: `admin`, `123456`, `password`  
❌ 个人信息: 姓名、生日、手机号  
❌ 简单规律: `abcd1234`, `12341234`  
❌ 默认密码: 保持默认配置（仅供开发测试）  

## 🚨 安全风险提示

### 高风险场景

⚠️ **默认密码**: 使用默认授权码 `eID6g1ka71A-p7UVNgwpBRnIIjXiOvPp`  
⚠️ **公网暴露**: 将服务直接暴露到公网而不修改密码  
⚠️ **密码泄露**: 将 `.env` 文件提交到公开代码仓库  
⚠️ **弱密码**: 使用过短或过于简单的密码  

### 防护措施

✅ **立即修改**: 首次部署后立即修改默认密码  
✅ **定期更换**: 每 3-6 个月更换一次授权码  
✅ **访问控制**: 使用防火墙限制访问来源  
✅ **HTTPS**: 生产环境使用 HTTPS 加密传输  
✅ **日志监控**: 定期检查登录日志，发现异常及时处理  

## 🔒 生产环境部署

### 1. 使用 HTTPS

```bash
# 使用 Nginx 反向代理
server {
    listen 443 ssl;
    server_name rss-admin.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 限制访问来源

```bash
# Nginx IP 白名单
location / {
    allow 192.168.1.0/24;  # 允许内网访问
    deny all;               # 拒绝其他所有
    
    proxy_pass http://localhost:5002;
}
```

### 3. 使用强密码

```bash
# 生成并配置 32 位随机密码
openssl rand -base64 32 > /root/.rss_admin_secret
export RSS_ADMIN_AUTH_CODE=$(cat /root/.rss_admin_secret)
```

### 4. 配置防火墙

```bash
# 只允许特定 IP 访问 5002 端口
ufw allow from 192.168.1.0/24 to any port 5002
ufw deny 5002
```

## 🔍 安全审计

### 检查清单

- [ ] 已修改默认授权码
- [ ] 授权码长度 ≥ 20 字符
- [ ] 授权码包含大小写字母、数字、特殊字符
- [ ] `.env` 文件未提交到 Git（已添加到 .gitignore）
- [ ] 生产环境使用 HTTPS
- [ ] 配置了访问来源限制
- [ ] 定期更换授权码
- [ ] 开启了防火墙规则

### 验证步骤

1. **测试未授权访问**:
```bash
curl http://localhost:5002/api/sources
# 应返回 401 错误
```

2. **测试错误密码**:
```bash
curl -X POST http://localhost:5002/login \
  -H "Content-Type: application/json" \
  -d '{"auth_code": "wrong-password"}'
# 应返回 401 错误
```

3. **测试正确密码**:
```bash
curl -X POST http://localhost:5002/login \
  -H "Content-Type: application/json" \
  -d '{"auth_code": "your-correct-password"}'
# 应返回 200 成功
```

## 📞 安全事件响应

### 发现密码泄露

1. **立即更换授权码**:
```bash
# 生成新密码
NEW_PASSWORD=$(openssl rand -base64 32)

# 更新配置
echo "RSS_ADMIN_AUTH_CODE=$NEW_PASSWORD" > .env

# 重启服务
./start.sh
```

2. **清除所有 Session**:
```bash
# 重启服务会自动清除所有 Session
docker compose restart rss-admin
```

3. **检查访问日志**:
```bash
# 查看最近的登录记录
grep "login" /var/log/rss-admin/*.log
```

### 发现异常访问

1. **临时禁用服务**:
```bash
docker compose stop rss-admin
```

2. **检查日志**:
```bash
docker compose logs rss-admin | grep "401\|403"
```

3. **加强防护后重启**:
```bash
# 更换密码 + 配置 IP 白名单
docker compose up -d rss-admin
```

## 📚 相关资源

- [OWASP 密码安全](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Flask Session 安全](https://flask.palletsprojects.com/en/3.0.x/security/)
- [环境变量最佳实践](https://12factor.net/config)

## ⚖️ 责任声明

本系统提供基础的鉴权保护，但安全性最终取决于：
- 授权码的强度和保密性
- 部署环境的网络安全配置
- 管理员的安全意识

请务必遵循本文档的安全建议，在生产环境中采取适当的安全措施。
