# RSS + n8n + 大模型筛选项目需求文档

## 项目概述
基于今天看啥 RSS 服务订阅微信公众号，通过 n8n 工作流调用大模型进行智能筛选，将符合 AI 主题的文章推送到企业微信。

---

## 1. 数据源层

### 1.1 今天看啥 RSS 服务
- **订阅数量**: < 200 个公众号
- **推荐套餐**: VIP-3 (150个账号/年) 或 VIP-6 (450个账号/年)
- **费用**: 450元/年 或 900元/年
- **RSS 格式**: Atom/RSS 2.0

### 1.2 RSS 源配置
每个公众号生成独立 RSS 链接，格式：
```
https://rsshub.app/jintiankansha/{公众号ID}
```

---

## 2. 工作流层 (n8n)

### 2.1 触发机制
- **检查频率**: 每小时检查一次 RSS 更新
- **推送时间**: 每天 3 个时间点推送
  - 09:00 (早间推送)
  - 13:00 (午间推送)
  - 20:00 (晚间推送)

### 2.2 批处理逻辑
```
每小时检查 -> 收集新文章 -> 暂存队列 
-> 到达推送时间点 -> 批量处理(10-20篇) 
-> 大模型筛选 -> 企业微信推送
```

### 2.3 数据处理流程
1. **RSS 抓取节点**: 获取所有订阅公众号的最新文章
2. **聚合节点**: 合并多个 RSS 源的文章
3. **批处理节点**: 每批 10-20 篇文章
4. **大模型筛选节点**: 调用 AI 判断相关性
5. **格式化节点**: 整理推送内容
6. **企业微信推送节点**: 发送消息

---

## 3. 大模型筛选层

### 3.1 API 配置
```bash
curl -X POST http://your-llm-api-host/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_LLM_API_KEY" \
  -d '{
    "prompt": "{筛选提示词}",
    "print": true,
    "model": "kimi-k2.5-ioa",
    "dangerouslySkipPermissions": true
  }'
```

### 3.2 筛选规则 (可配置)
**后台配置文件**: `config/keywords.json`

```json
{
  "categories": [
    {
      "name": "AIGC",
      "keywords": ["生成式AI", "AIGC", "内容生成", "文生图", "文生视频"],
      "description": "生成式人工智能内容"
    },
    {
      "name": "AI初创",
      "keywords": ["AI初创", "AI公司", "AI创业", "AI企业", "AI团队"],
      "description": "AI初创公司动态"
    },
    {
      "name": "AI融资",
      "keywords": ["AI融资", "AI投资", "AI估值", "AI IPO", "AI并购"],
      "description": "AI领域投融资新闻"
    },
    {
      "name": "大模型",
      "keywords": ["大模型", "LLM", "GPT", "Claude", "Transformer"],
      "description": "大语言模型技术进展"
    },
    {
      "name": "AI产品",
      "keywords": ["AI产品", "AI应用", "AI工具", "AI助手", "AI Agent"],
      "description": "AI产品发布和评测"
    }
  ],
  "match_mode": "semantic",
  "threshold": 0.7
}
```

### 3.3 大模型提示词模板
```
你是一位专业的 AI 领域内容筛选助手。

任务：判断以下文章是否与 AI 相关，并分类。

筛选规则（语义匹配，非关键词精确匹配）：
{config_categories}

待筛选文章：
{batch_articles}

请输出 JSON 格式：
{
  "results": [
    {
      "index": 1,
      "title": "文章标题",
      "relevant": true/false,
      "categories": ["AI融资", "大模型"],
      "reason": "简要说明匹配原因",
      "confidence": 0.85
    }
  ]
}
```

---

## 4. 推送层

### 4.1 企业微信机器人配置
- **Webhook URL**: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_WECHAT_WEBHOOK_KEY`
- **消息格式**: Markdown

### 4.2 推送内容格式
```markdown
## 📰 AI 资讯精选 ({日期} {时段})

本期筛选 {总文章数} 篇，命中 {匹配数} 篇

---

### 1. {文章标题}
**分类**: {AI融资} | {大模型}
**公众号**: {来源}
**摘要**: {文章摘要前100字}...
[阅读原文]({文章链接})

---

### 2. {文章标题}
...

---

*Powered by n8n + 大模型筛选*
```

---

## 5. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      今天看啥 RSS (200个公众号)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ RSS Feed
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                           n8n 工作流                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │  Cron 触发器  │    │ RSS 抓取节点  │    │ 文章聚合节点  │        │
│  │ (每小时)     │ -> │ (HTTP Request)│ -> │ (Merge)      │        │
│  └──────────────┘    └──────────────┘    └──────┬───────┘        │
│                                                  │               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐        │
│  │ 企业微信推送  │ <- │ 格式化节点    │ <- │ 大模型筛选    │        │
│  │ (Webhook)    │    │ (Markdown)   │    │ (HTTP)       │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│                                                                  │
│  推送时间: 09:00 / 13:00 / 20:00                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 部署配置

### 6.1 n8n Docker 部署
```yaml
# docker-compose.yml
version: '3'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-rss-ai
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_password
      - WEBHOOK_URL=https://your-domain.com/
    volumes:
      - ./n8n-data:/home/node/.n8n
      - ./config:/config
    restart: always
```

### 6.2 配置文件结构
```
n8n/
├── docker-compose.yml
├── requirements.md
├── config/
│   ├── keywords.json          # 筛选规则配置
│   ├── rss-sources.json       # RSS 源列表
│   └── wechat-config.json     # 企业微信配置
├── n8n-workflows/
│   └── rss-ai-filter.json     # 工作流导出文件
└── logs/
    └── app.log
```

---

## 7. 关键节点设计

### 7.1 Cron 节点配置
```json
{
  "name": "Schedule Trigger",
  "type": "n8n-nodes-base.scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [
        {"hour": 9, "minute": 0},
        {"hour": 13, "minute": 0},
        {"hour": 20, "minute": 0}
      ]
    }
  }
}
```

### 7.2 HTTP Request 节点 (大模型)
```json
{
  "name": "AI Filter",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://your-llm-api-host/agent",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer YOUR_LLM_API_KEY"
    },
    "body": {
      "prompt": "={{ $json.prompt }}",
      "model": "kimi-k2.5-ioa",
      "print": true,
      "dangerouslySkipPermissions": true
    }
  }
}
```

### 7.3 企业微信推送节点
```json
{
  "name": "WeChat Work",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_WECHAT_WEBHOOK_KEY",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "msgtype": "markdown",
      "markdown": {
        "content": "={{ $json.formattedMessage }}"
      }
    }
  }
}
```

---

## 8. 待办事项

- [ ] 购买今天看啥 VIP-3/VIP-6 套餐
- [ ] 部署 n8n 服务
- [ ] 配置 RSS 源列表 (200个公众号)
- [ ] 编写大模型筛选提示词
- [ ] 创建 n8n 工作流
- [ ] 测试端到端流程
- [ ] 配置监控告警

---

## 9. 注意事项

1. **API 安全**: 大模型 API Key 需要妥善保管，建议通过 n8n 的 Credentials 管理
2. **频率限制**: 注意大模型 API 的调用频率限制
3. **企业微信限制**: 机器人消息有频率限制（20条/秒）
4. **成本控制**: 200个公众号每小时检查，预计每天 API 调用次数需要评估

---

*文档版本: v1.0*
*创建时间: 2026-02-20*
