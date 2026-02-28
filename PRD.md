# 项目需求文档 (PRD)

## 项目名称
RSS智能筛选推送系统

## 项目目标
通过今天看啥RSS服务订阅公众号，使用n8n工作流结合大模型进行智能内容筛选，将符合AI主题的文章推送到企业微信。

---

## 1. 需求概述

### 1.1 核心功能
- 订阅200个以内公众号（今天看啥VIP-6套餐：450个额度）
- 每小时检查RSS更新
- 大模型语义筛选（非关键词匹配）
- 定时推送：9:00、13:00、20:00
- 推送到企业微信机器人

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        今天看啥 RSS                              │
│                    (订阅 <200 个公众号)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ RSS Feed
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                           n8n 工作流                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 每小时触发   │ -> │ 获取RSS     │ -> │ 缓存待处理文章      │  │
│  │ (Cron: 0 *  │    │ (HTTP Node) │    │ (SQLite/Postgres)   │  │
│  │  * * *)     │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                       │          │
│  ┌────────────────────────────────────────────────────┘          │
│  │                                                               │
│  ▼                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 批处理      │ -> │ 大模型筛选   │ -> │ 缓存筛选结果        │  │
│  │ (10-20篇)   │    │ (HTTP curl) │    │ (符合规则的文章)    │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                       │          │
│  ┌────────────────────────────────────────────────────┘          │
│  │                                                               │
│  ▼                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 定时推送    │ -> │ 格式化消息   │ -> │ 企业微信Webhook     │  │
│  │ (9/13/20点) │    │ (Markdown)  │    │ POST请求            │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 详细需求

### 2.1 数据源配置

#### 2.1.1 今天看啥RSS
- **套餐**: VIP-6（900元/年，450个订阅额度）
- **订阅数量**: < 200个公众号
- **输出格式**: RSS 2.0 / Atom
- **更新频率**: 由今天看啥控制（通常几分钟到几小时）

#### 2.1.2 RSS源配置示例
```yaml
rss_sources:
  - name: "AI大模型日报"
    url: "https://rsshub.app/jintiankansha/xxx"
    category: "AI技术"
  - name: "投资界"
    url: "https://rsshub.app/jintiankansha/yyy"
    category: "投资融资"
```

### 2.2 n8n工作流设计

#### 2.2.1 触发器配置
```json
{
  "trigger": "cron",
  "schedule": "0 * * * *",
  "description": "每小时检查RSS更新"
}
```

#### 2.2.2 推送触发器
```json
{
  "trigger": "cron",
  "schedule": "0 9,13,20 * * *",
  "description": "每天9点、13点、20点推送"
}
```

#### 2.2.3 工作流节点

| 节点 | 类型 | 功能 |
|------|------|------|
| Cron Trigger | Trigger | 每小时触发 |
| HTTP Request | Action | 获取RSS feed |
| Function | Action | 解析RSS，提取文章 |
| Postgres/SQLite | Action | 存储待处理文章 |
| Batch | Action | 每批10-20篇处理 |
| HTTP Request | Action | 调用大模型API |
| Function | Action | 解析大模型返回 |
| Postgres/SQLite | Action | 存储筛选结果 |
| Cron Trigger | Trigger | 定时推送触发 |
| Function | Action | 格式化消息 |
| HTTP Request | Action | 推送到企业微信 |

### 2.3 大模型筛选规则

#### 2.3.1 API配置
```bash
curl -X POST http://your-llm-api-host/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_LLM_API_KEY" \
  -d '{
    "prompt": "[筛选提示词]",
    "print": true,
    "model": "kimi-k2.5-ioa",
    "dangerouslySkipPermissions": true
  }'
```

#### 2.3.2 筛选提示词模板
```
你是一位AI领域内容筛选专家。请判断以下文章是否与AI相关。

## 筛选主题（语义匹配，非关键词）：
- AIGC / 生成式AI
- AI初创公司动态
- AI融资/投资新闻
- AI创业相关
- 大模型技术进展
- AI产品发布
- 人工智能行业趋势

## 后台配置关键词（需语义泛化理解）：
{{keywords}}

## 待筛选文章：
{{articles}}

## 输出格式（JSON）：
{
  "articles": [
    {
      "index": 1,
      "relevant": true/false,
      "confidence": 0.95,
      "reason": "符合AI融资主题",
      "matched_concept": "AI投资"
    }
  ]
}

注意：
1. 使用语义理解，不要仅关键词匹配
2. 考虑上下文和文章主旨
3. 置信度>0.7才标记为相关
```

#### 2.3.3 后台关键词配置
```json
{
  "keywords": [
    "AIGC",
    "生成式AI",
    "大模型",
    "AI融资",
    "AI投资",
    "AI创业",
    "人工智能",
    "LLM",
    "ChatGPT",
    "Claude"
  ],
  "semantic_rules": {
    "AIGC": ["内容生成", "AI绘画", "AI写作", "AI视频"],
    "AI融资": ["融资", "投资", "估值", "独角兽", "VC", "PE"],
    "AI创业": ["创业", "初创公司", "创始人", "CEO", " startup"]
  }
}
```

### 2.4 企业微信推送

#### 2.4.1 Webhook配置
```
POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_WECHAT_WEBHOOK_KEY
```

#### 2.4.2 消息格式（Markdown）
```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "**AI资讯精选** \n> 推送时间：{{timestamp}}\n> 共 {{count}} 篇文章\n\n---\n\n**1. {{title_1}}**\n> {{summary_1}}\n> [阅读原文]({{url_1}})\n\n**2. {{title_2}}**\n> {{summary_2}}\n> [阅读原文]({{url_2}})\n\n---\n\n*由 RSS智能筛选系统推送*"
  }
}
```

---

## 3. 数据模型

### 3.1 文章表 (articles)
```sql
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  url TEXT NOT NULL,
  summary TEXT,
  source VARCHAR(100),
  publish_time TIMESTAMP,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed BOOLEAN DEFAULT FALSE,
  relevant BOOLEAN,
  confidence FLOAT,
  reason TEXT,
  matched_concept VARCHAR(100),
  pushed BOOLEAN DEFAULT FALSE,
  pushed_at TIMESTAMP
);
```

### 3.2 配置表 (config)
```sql
CREATE TABLE config (
  id SERIAL PRIMARY KEY,
  key VARCHAR(100) UNIQUE NOT NULL,
  value TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始配置
INSERT INTO config (key, value) VALUES
('keywords', '["AIGC", "生成式AI", "大模型", "AI融资", "AI投资"]'),
('batch_size', '15'),
('confidence_threshold', '0.7'),
('push_times', '["09:00", "13:00", "20:00"]');
```

---

## 4. 部署配置

### 4.1 Docker Compose
```yaml
version: '3'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-rss
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_password
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=n8n_password
    volumes:
      - ./n8n-data:/home/node/.n8n
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    container_name: n8n-postgres
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=n8n_password
      - POSTGRES_DB=n8n
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  # 可选：用于存储文章数据
  redis:
    image: redis:7-alpine
    container_name: n8n-redis
    restart: always
    volumes:
      - ./redis-data:/data
```

### 4.2 环境变量
```bash
# .env 文件
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

POSTGRES_USER=n8n
POSTGRES_PASSWORD=n8n_password
POSTGRES_DB=n8n

# 大模型API
LLM_API_URL=http://your-llm-api-host/agent
LLM_API_KEY=YOUR_LLM_API_KEY
LLM_MODEL=kimi-k2.5-ioa

# 企业微信
WECHAT_WEBHOOK_KEY=YOUR_WECHAT_WEBHOOK_KEY
```

---

## 5. 实施计划

### Phase 1: 基础环境 (Day 1)
- [ ] 部署 n8n + Postgres
- [ ] 配置今天看啥RSS订阅
- [ ] 测试RSS获取

### Phase 2: 核心工作流 (Day 2)
- [ ] 创建每小时检查工作流
- [ ] 实现文章存储逻辑
- [ ] 测试数据流

### Phase 3: 大模型集成 (Day 3)
- [ ] 集成大模型API调用
- [ ] 实现筛选逻辑
- [ ] 测试筛选准确性

### Phase 4: 推送功能 (Day 4)
- [ ] 实现定时推送工作流
- [ ] 格式化企业微信消息
- [ ] 测试端到端流程

### Phase 5: 优化 (Day 5)
- [ ] 添加监控告警
- [ ] 优化提示词
- [ ] 文档完善

---

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 今天看啥服务不稳定 | 高 | 准备备用RSS源 |
| 大模型API限流 | 中 | 实现请求队列和重试 |
| 企业微信Webhook限流 | 中 | 批量推送，控制频率 |
| 大模型筛选不准确 | 中 | 持续优化提示词，人工反馈 |
| 数据量过大 | 低 | 定期清理历史数据 |

---

## 7. 后续优化方向

1. **Web管理后台**：可视化配置关键词、查看筛选统计
2. **多模型对比**：同时调用多个模型，投票决定
3. **智能摘要**：大模型生成文章摘要
4. **分类推送**：不同主题推送到不同企业微信群
5. **阅读统计**：追踪文章点击阅读情况

---

文档版本: v1.0
创建时间: 2026-02-20
最后更新: 2026-02-20
