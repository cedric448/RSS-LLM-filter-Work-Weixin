# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## 项目概述

RSS 智能筛选推送系统 - 使用 n8n 工作流 + 大模型进行内容筛选，将符合 AI 主题的公众号文章推送到企业微信。

**技术栈**: n8n (workflow automation), Docker, Python (Mock RSS Server), PostgreSQL

## 项目架构

```
今天看啥 RSS (<200 公众号) 
    ↓ RSS Feed
n8n 工作流
    ├─ Schedule Trigger (每小时检查)
    ├─ Fetch RSS Articles (HTTP Request)
    ├─ Batch Processor (10-20篇/批)
    ├─ Build AI Prompt (构建提示词)
    ├─ AI Filter (调用大模型筛选)
    ├─ Format Message (格式化 Markdown)
    └─ WeChat Work Push (企业微信推送)
    
定时推送: 9:00, 13:00, 20:00
```

## 开发与部署命令

### Docker 容器管理

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs n8n
docker compose logs mock-rss-server

# 重启 n8n (应用配置更改后)
docker compose restart n8n

# 停止所有服务
docker compose down
```

### n8n API 操作

```bash
# API Key (存储在环境变量中)
N8N_API_KEY="n8n_api_77e85106b2f5dea8d104fb2176a4f0fd7f214eb0beff33a40bfc3c8a54ec3b8e481a2cccacfec12e"

# 列出所有工作流
curl -s "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# 获取工作流详情
curl -s "http://localhost:5678/api/v1/workflows/{workflow_id}" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# 激活/停用工作流
curl -X PATCH "http://localhost:5678/api/v1/workflows/{workflow_id}" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"active": true}'

# 手动执行工作流
curl -X POST "http://localhost:5678/api/v1/workflows/{workflow_id}/execute" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Mock RSS Server

```bash
# 测试 RSS API
curl http://localhost:5001/api/articles

# 查看配置
cat config/rss-sources.json
cat config/keywords.json
```

## 核心配置文件

### docker-compose.yml

- **n8n 服务**: 端口 5678, 使用 n8nio/n8n:1.48.0
- **mock-rss-server**: 端口 5001 (映射到容器内 5000)
- **postgres**: 端口 5432, 数据库存储

重要环境变量:
- `N8N_SECURE_COOKIE=false` - 允许非 HTTPS 访问
- `N8N_BASIC_AUTH_USER=admin`
- `N8N_BASIC_AUTH_PASSWORD=n8n_password_2026`

### 工作流文件

`n8n-workflows/rss-ai-filter-workflow.json` - 主工作流定义

关键节点:
1. **Schedule Trigger**: 每小时触发 (cron: 0 * * * *)
2. **Fetch RSS Articles**: GET http://localhost:5001/api/articles
3. **Batch Processor**: 检查推送时间 (8:55, 12:55, 19:55)，每批15篇
4. **Build AI Prompt**: 构建大模型筛选提示词
5. **AI Filter**: POST http://43.132.153.123/agent
   - Model: kimi-k2.5-ioa
   - Authorization: Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4
6. **Format Message**: 解析 AI 响应，格式化 Markdown 消息
7. **WeChat Work Push**: POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=defd0b35-256b-40ba-a513-c21feb5955a5

### 筛选规则配置

`config/keywords.json` - 定义文章分类和关键词:
- AIGC: 生成式AI、内容生成、文生图、文生视频
- AI初创: AI公司、AI创业、AI企业
- AI融资: AI投资、AI估值、AI IPO
- 大模型: LLM、GPT、Claude、Transformer
- AI产品: AI应用、AI工具、AI助手、AI Agent

**重要**: 使用语义匹配而非关键词精确匹配

## 工作流导入

```bash
# 清理工作流 JSON (移除只读字段)
python3 -c "
import json
with open('n8n-workflows/rss-ai-filter-workflow.json', 'r') as f:
    data = json.load(f)
for key in ['tags', 'id', 'createdAt', 'updatedAt', 'versionId', 'meta', 'pinData', 'staticData']:
    data.pop(key, None)
with open('/tmp/workflow_clean.json', 'w') as f:
    json.dump(data, f)
"

# 导入工作流
curl -X POST "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/workflow_clean.json
```

## 故障排查

### n8n 容器启动失败

检查环境变量配置，特别是 `N8N_SECURE_COOKIE=false`

### mock-rss-server 重启循环

可能是权限问题或端口冲突:
```bash
# 查看日志
docker compose logs mock-rss-server --tail 50

# 释放端口
lsof -ti:5001 | xargs kill -9
```

### 工作流推送时间不生效

检查 Batch Processor 节点的时间判断逻辑:
- 推送时间前5分钟触发 (8:55, 12:55, 19:55)
- 容器时区设置: `GENERIC_TIMEZONE=Asia/Shanghai`

### 大模型 API 调用失败

检查:
1. API Key 是否正确
2. 网络连接到 http://43.132.153.123
3. 请求体格式是否符合要求

## 数据流说明

1. **RSS 获取**: 从 mock-rss-server 获取文章列表 (生产环境替换为真实 RSS 源)
2. **时间过滤**: 只在推送时间点前5分钟内处理文章
3. **批量处理**: 每批15篇文章，避免 API 超时
4. **AI 筛选**: 大模型判断文章与 AI 主题相关性，返回 JSON 格式结果
5. **结果解析**: 提取相关文章，生成分类标签和推荐理由
6. **消息格式化**: 使用 Markdown 格式，包含标题、分类、摘要、链接
7. **企业微信推送**: Webhook 方式发送到群聊

## 重要注意事项

1. **API Key 安全**: 
   - n8n API Key: 通过环境变量或 n8n Credentials 管理
   - 大模型 API Key: 存储在工作流节点中，避免提交到代码库

2. **推送频率限制**:
   - 企业微信机器人: 20条/秒
   - 大模型 API: 根据供应商限制调整批次大小

3. **工作流版本管理**:
   - 通过 n8n UI 导出工作流到 `n8n-workflows/` 目录
   - 提交前检查是否包含敏感信息

4. **测试环境**:
   - 使用 mock-rss-server 进行本地测试
   - 生产环境配置真实 RSS 源 URL

## 相关文档

- PRD.md - 详细产品需求文档
- requirements.md - 技术需求说明
- n8n 官方文档: https://docs.n8n.io/
- 今天看啥 RSS: https://www.jintiankansha.me/
