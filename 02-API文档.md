# API 接口文档

## 1. 外部 API 依赖

### 1.1 今天看啥 API4 接口

#### 接口信息
- **Base URL**: `http://www.jintiankansha.me/api3/query`
- **认证方式**: URL参数 (user + token)
- **用途**: 获取公众号文章列表

#### 1.1.1 获取专栏文章

**接口**: `GET /api3/query/get_topics_by_one_column`

**请求参数**:
```json
{
  "user": "your-email@example.com",
  "token": "YOUR_API4_TOKEN",
  "slug": "ai-frontiers"    // 公众号slug
}
```

**成功响应** (200):
```json
{
  "status": "success",
  "data": [
    {
      "name": "文章标题",
      "original_url": "https://mp.weixin.qq.com/s/xxx",
      "publish_time": "20260223090000",
      "image": "https://xxx.jpg"
    }
  ]
}
```

**失败响应** (404/503):
```json
{
  "status": "error",
  "data": {
    "message": "请求过快，请稍后再试"
  }
}
```

**限流规则**:
- 返回状态码: 404 或 503
- 响应体包含: "too fast" 或 "频率" 关键词
- 建议间隔: 1秒/请求

**重试策略**:
```python
# 指数退避重试
重试次数: 3次
重试间隔: 3秒, 6秒, 12秒
```

---

### 1.2 大模型筛选 API

#### 接口信息
- **URL**: `http://your-llm-api-host/agent`
- **认证方式**: Bearer Token
- **模型**: kimi-k2.5-ioa
- **用途**: AI 智能筛选文章

#### 1.2.1 文章筛选

**接口**: `POST /agent`

**请求头**:
```http
Content-Type: application/json
Authorization: Bearer YOUR_LLM_API_KEY
```

**请求体**:
```json
{
  "model": "kimi-k2.5-ioa",
  "messages": [
    {
      "role": "user",
      "content": "{筛选提示词}"
    }
  ],
  "print": true,
  "dangerouslySkipPermissions": true
}
```

**提示词格式**:
```text
你是一位AI领域内容筛选专家。请判断以下文章是否与AI相关。

## 筛选主题（语义匹配）：
- AIGC / 生成式AI
- AI初创公司动态
- AI融资/投资新闻
- 大模型技术进展
- AI产品发布

## 后台配置关键词：
{从 config/keywords.json 读取}

## 待筛选文章：
1. 标题: xxx
   来源: xxx
   摘要: xxx

2. 标题: yyy
   ...

## 输出格式（JSON）：
{
  "articles": [
    {
      "index": 1,
      "relevant": true/false,
      "categories": ["AI融资", "大模型"],
      "reason": "文章讨论了某AI公司获得B轮融资",
      "confidence": 0.85
    }
  ]
}

注意：
1. 使用语义理解，不要仅关键词匹配
2. 置信度>0.7才标记为相关
```

**成功响应**:
```json
{
  "choices": [
    {
      "message": {
        "content": "{\"articles\": [{\"index\": 1, \"relevant\": true, ...}]}"
      }
    }
  ]
}
```

**错误处理**:
- 超时: 15秒
- 重试: 不重试 (由调用方决定)
- 解析失败: 返回空数组

---

### 1.3 企业微信 Webhook API

#### 接口信息
- **URL**: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={KEY}`
- **Webhook Key**: `YOUR_WECHAT_WEBHOOK_KEY`
- **用途**: 推送消息到企业微信群聊

#### 1.3.1 发送 Markdown 消息

**接口**: `POST /cgi-bin/webhook/send`

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "📰 **AI前线 | AIGC**\n[GPT-5即将发布](https://xxx)\n\n💡 推荐理由: OpenAI宣布GPT-5将于下月发布"
  }
}
```

**成功响应** (200):
```json
{
  "errcode": 0,
  "errmsg": "ok"
}
```

**失败响应**:
```json
{
  "errcode": 93000,
  "errmsg": "invalid webhook url"
}
```

**限流规则**:
- 频率限制: 20条/秒
- 消息长度: 最大 4096 字节
- 格式要求: 标准 Markdown

**消息格式规范**:
```markdown
📰 **{来源} | {分类1} | {分类2}**
[{文章标题}]({文章链接})

💡 推荐理由: {AI生成的推荐理由}
```

---

## 2. 内部模块接口

### 2.1 llm_filter.py

#### 2.1.1 filter_articles_batch()

**函数签名**:
```python
def filter_articles_batch(articles: List[Dict]) -> List[Dict]
```

**参数**:
```python
articles = [
    {
        'title': '文章标题',
        'link': 'https://xxx',
        'summary': '文章摘要',
        'source_name': 'AI前线'
    }
]
```

**返回值**:
```python
[
    {
        'title': '文章标题',
        'link': 'https://xxx',
        'summary': '文章摘要',
        'source_name': 'AI前线',
        'categories': ['AIGC', '大模型'],    # 新增
        'reason': '推荐理由',                # 新增
        'confidence': 0.85                   # 新增
    }
]
```

**异常**:
- `requests.RequestException`: API调用失败
- `json.JSONDecodeError`: 响应解析失败
- `KeyError`: 响应格式错误

---

### 2.2 wechat_pusher.py

#### 2.2.1 push_articles()

**函数签名**:
```python
def push_articles(articles: List[Dict]) -> bool
```

**参数**:
```python
articles = [
    {
        'title': '文章标题',
        'link': 'https://xxx',
        'source_name': 'AI前线',
        'categories': ['AIGC'],
        'reason': '推荐理由'
    }
]
```

**返回值**:
- `True`: 推送成功
- `False`: 推送失败

**异常**:
- `requests.RequestException`: Webhook调用失败

#### 2.2.2 format_message()

**函数签名**:
```python
def format_message(articles: List[Dict]) -> str
```

**返回值**:
```markdown
📰 **AI前线 | AIGC**
[文章标题](https://xxx)

💡 推荐理由: ...

---

📰 **投资界 | AI融资**
[另一篇文章](https://yyy)

💡 推荐理由: ...
```

---

### 2.3 auto_push.py

#### 2.3.1 核心函数

##### init_database()
```python
def init_database() -> None
```
初始化 SQLite 去重数据库,创建表和索引。

##### get_rss_sources()
```python
def get_rss_sources() -> List[Dict]
```
从 `config/rss-sources.json` 读取启用的 RSS 源。

**返回值**:
```python
[
    {
        'name': 'AI前线',
        'slug': 'ai-frontiers',
        'url': 'https://xxx',
        'enabled': True
    }
]
```

##### is_article_pushed()
```python
def is_article_pushed(article: Dict) -> bool
```
检查文章是否已推送 (基于哈希)。

##### mark_articles_as_pushed()
```python
def mark_articles_as_pushed(articles: List[Dict]) -> None
```
标记文章为已推送,写入数据库。

##### clean_old_history()
```python
def clean_old_history() -> int
```
清理 30 天前的历史记录,返回删除数量。

##### fetch_articles_via_api4()
```python
def fetch_articles_via_api4(
    slug: str,
    source_name: str,
    retry_count: int = 0
) -> List[Dict]
```
通过 API4 获取文章,支持重试。

**返回值**:
```python
[
    {
        'title': '文章标题',
        'link': 'https://xxx',
        'summary': '',
        'source_name': 'AI前线',
        'publish_time': '20260223090000',
        'image': 'https://xxx.jpg'
    }
]
```

---

## 3. 配置文件格式

### 3.1 config/rss-sources.json

```json
{
  "sources": [
    {
      "name": "AI前线",           // 必填: 源名称
      "slug": "ai-frontiers",    // 必填: API4 slug
      "url": "https://xxx",      // 可选: RSS URL (RSS模式使用)
      "enabled": true            // 必填: 是否启用
    }
  ]
}
```

### 3.2 config/keywords.json

```json
{
  "categories": [
    {
      "name": "AIGC",                              // 分类名称
      "keywords": ["生成式AI", "内容生成"],         // 关键词列表
      "description": "生成式人工智能内容"           // 描述
    }
  ],
  "match_mode": "semantic",                        // 匹配模式: semantic/keyword
  "threshold": 0.7                                 // 置信度阈值
}
```

---

## 4. 错误码

### 4.1 今天看啥 API

| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| 404 | 限流或slug不存在 | 检查响应体,包含"too fast"则重试 |
| 503 | 服务限流 | 3秒后重试 |
| 200 + error | 业务错误 | 检查data.message |

### 4.2 企业微信 API

| errcode | 说明 | 处理方式 |
|---------|------|---------|
| 0 | 成功 | - |
| 93000 | 无效的webhook | 检查key参数 |
| 93004 | 请求过快 | 降低频率 |
| 301005 | 消息长度超限 | 分批发送 |

---

## 5. 性能指标

### 5.1 API 响应时间

| API | 平均响应时间 | P95 响应时间 | 超时设置 |
|-----|------------|-------------|---------|
| 今天看啥 API4 | 500ms | 2s | 10s |
| 大模型 API | 3s | 10s | 15s |
| 企业微信 API | 200ms | 500ms | 5s |

### 5.2 限流配置

| 系统 | 限流规则 | 应对策略 |
|------|---------|---------|
| 今天看啥 | 未公开 | 1秒/请求间隔 |
| 大模型 | 未知 | 批量处理降低请求数 |
| 企业微信 | 20条/秒 | 批量合并消息 |

---

## 6. 测试示例

### 6.1 测试今天看啥 API

```bash
curl -X GET "http://www.jintiankansha.me/api3/query/get_topics_by_one_column" \
  -G \
  --data-urlencode "user=your-email@example.com" \
  --data-urlencode "token=YOUR_API4_TOKEN" \
  --data-urlencode "slug=ai-frontiers"
```

### 6.2 测试大模型 API

```bash
curl -X POST "http://your-llm-api-host/agent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_LLM_API_KEY" \
  -d '{
    "model": "kimi-k2.5-ioa",
    "messages": [{
      "role": "user",
      "content": "测试消息"
    }]
  }'
```

### 6.3 测试企业微信 Webhook

```bash
curl -X POST "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_WECHAT_WEBHOOK_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "msgtype": "markdown",
    "markdown": {
      "content": "**测试消息**\n这是一条测试消息"
    }
  }'
```

---

**文档版本**: v1.0  
**创建时间**: 2026-02-23  
**最后更新**: 2026-02-23
