# 环境配置指南

## 概述

本项目需要配置多个 API 密钥和 Token。所有敏感信息都应通过环境变量传递,不要直接硬编码在代码中。

## 必需的环境变量

### 1. 今天看啥 API 配置

访问 [今天看啥](https://www.jintiankansha.me/) 注册账号并获取 API 凭证。

```bash
export API4_USER="your-email@example.com"
export API4_TOKEN="your-api-token-here"
```

### 2. 大模型 API 配置

配置你的 LLM API 服务地址和认证信息:

```bash
export LLM_API_URL="http://your-llm-api-endpoint"
export LLM_API_KEY="Bearer your-llm-api-key-here"
```

支持的模型: Kimi, Claude, GPT 等支持 JSON 格式响应的模型。

### 3. 企业微信 Webhook 配置

在企业微信群中创建机器人并获取 Webhook Key:

1. 打开企业微信群
2. 点击群设置 → 群机器人
3. 添加机器人并复制 Webhook URL 中的 key 参数

```bash
export WECHAT_WEBHOOK_KEY="your-webhook-key-here"
```

### 4. Flask 管理后台配置

```bash
# Flask Secret Key (用于 session 加密)
# 生成方法: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
export FLASK_SECRET_KEY="your-flask-secret-key-here"

# 管理后台登录密码
export RSS_ADMIN_AUTH_CODE="your-admin-password-here"
```

### 5. n8n 配置 (可选)

如果使用 n8n 工作流模式:

```bash
export N8N_API_KEY="your-n8n-api-key-here"
export N8N_BASIC_AUTH_USER="admin"
export N8N_BASIC_AUTH_PASSWORD="your-n8n-password-here"
```

## 配置方法

### 方式 1: 使用 .env 文件 (推荐)

1. 复制示例配置文件:
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件,填入你的实际配置:
```bash
vim .env
```

3. 在启动脚本中加载环境变量:
```bash
source .env
python3 src/auto_push.py
```

**注意**: `.env` 文件已在 `.gitignore` 中,不会被提交到 Git。

### 方式 2: 系统环境变量

将环境变量添加到 `~/.bashrc` 或 `~/.zshrc`:

```bash
# 添加到配置文件
cat >> ~/.bashrc << 'EOF'
# RSS 智能筛选推送系统环境变量
export API4_USER="your-email@example.com"
export API4_TOKEN="your-api-token-here"
export LLM_API_URL="http://your-llm-api-endpoint"
export LLM_API_KEY="Bearer your-llm-api-key-here"
export WECHAT_WEBHOOK_KEY="your-webhook-key-here"
export FLASK_SECRET_KEY="your-flask-secret-key-here"
export RSS_ADMIN_AUTH_CODE="your-admin-password-here"
EOF

# 重新加载配置
source ~/.bashrc
```

### 方式 3: Docker Compose

在 `docker-compose.yml` 中配置环境变量:

```yaml
services:
  app:
    environment:
      - API4_USER=${API4_USER}
      - API4_TOKEN=${API4_TOKEN}
      - LLM_API_URL=${LLM_API_URL}
      - LLM_API_KEY=${LLM_API_KEY}
      - WECHAT_WEBHOOK_KEY=${WECHAT_WEBHOOK_KEY}
```

## 验证配置

运行测试脚本验证配置是否正确:

```bash
# 测试今天看啥 API
curl -X POST "http://www.jintiankansha.me/api3/query/get_topics_by_one_column" \
  -d "user=$API4_USER&token=$API4_TOKEN&slug=pJMG8ZXFLd"

# 测试大模型 API
curl -X POST "$LLM_API_URL" \
  -H "Authorization: $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"your-model","messages":[{"role":"user","content":"测试"}]}'

# 测试企业微信 Webhook
curl -X POST "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=$WECHAT_WEBHOOK_KEY" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'
```

## 安全建议

1. ✅ **永远不要**将密钥提交到 Git 仓库
2. ✅ 使用 `.gitignore` 排除包含密钥的文件
3. ✅ 定期轮换 API 密钥和 Token
4. ✅ 使用强密码和复杂的 Secret Key
5. ✅ 限制 API 密钥的访问权限和 IP 白名单
6. ✅ 在生产环境使用环境变量或密钥管理服务

## 常见问题

### Q: 如何生成安全的 Secret Key?

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Q: 如何查看当前环境变量?

```bash
echo $API4_USER
env | grep API4
```

### Q: 企业微信 Webhook 发送失败?

检查:
1. Webhook Key 是否正确
2. 消息格式是否符合企业微信规范
3. 是否超过频率限制 (20条/分钟)

### Q: 大模型 API 调用失败?

检查:
1. API URL 和 Key 是否正确
2. 网络连接是否正常
3. API 配额是否用尽
4. 请求格式是否符合 API 规范

## 技术支持

如有问题,请查看:
- [项目文档](./README.md)
- [故障排查](./CODEBUDDY.md#故障排查)
- [GitHub Issues](https://github.com/cedric448/RSS-LLM-filter-Work-Weixin/issues)
