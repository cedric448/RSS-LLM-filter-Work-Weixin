# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## 项目概述

RSS 智能筛选推送系统 - 使用 Python + Cron + 大模型进行内容筛选，将符合 AI 主题的公众号文章推送到企业微信。

**技术栈**: Python 3, Cron, LLM API, SQLite, Flask (管理后台)

## 项目架构

```
今天看啥 API (<200 公众号) 
    ↓ API4 JSON 接口
Python 自动推送 (src/auto_push.py)
    ├─ Cron 定时触发 (9:00, 13:00, 20:00)
    ├─ API4 获取文章 (并发, 重试, 限流控制)
    ├─ 去重过滤 (SQLite 历史记录)
    ├─ AI 智能筛选 (LLM 批量处理, 15篇/批)
    ├─ 格式化消息 (Markdown)
    └─ 企业微信推送 (Webhook)
```

## 开发与部署命令

### 手动执行推送

```bash
# 加载环境变量并执行
/root/project-wb/n8n/run_auto_push.sh

# 或手动执行
cd /root/project-wb/n8n
source .env
python3 src/auto_push.py
```

### Cron 定时任务管理

```bash
# 查看定时任务
crontab -l | grep auto_push

# 编辑定时任务
crontab -e

# 当前配置: 每天 9:05, 13:05, 20:05
# 5 9,13,20 * * * /root/project-wb/n8n/run_auto_push.sh >> /root/project-wb/n8n/logs/auto_push.log 2>&1
```

### 查看日志

```bash
# 查看最近推送日志
tail -100 /root/project-wb/n8n/logs/auto_push.log

# 实时查看
tail -f /root/project-wb/n8n/logs/auto_push.log

# 查看今日推送结果
grep "$(date +%Y-%m-%d)" /root/project-wb/n8n/logs/auto_push.log | grep "推送完成" -A 5
```

### 管理后台

```bash
# 管理后台运行在 systemd 服务
systemctl status rss-admin

# 访问地址: https://<服务器IP>:8443
```

## 核心配置文件

### .env - 环境变量

```bash
API4_USER=xxx          # 今天看啥 API 账号
API4_TOKEN=xxx         # 今天看啥 API Token
LLM_API_URL=xxx        # 大模型 API 地址
LLM_API_KEY=xxx        # 大模型 API Key
WECHAT_WEBHOOK_KEY=xxx # 企业微信 Webhook Key
```

### config/rss-sources.json - RSS 源配置

每个源包含:
- `name`: 公众号名称
- `slug`: 今天看啥 API4 的源标识 (必需)
- `enabled`: 是否启用

### config/keywords.json - 筛选规则

定义文章分类和关键词:
- AIGC: 生成式AI、内容生成、文生图、文生视频
- AI初创: AI公司、AI创业、AI企业
- AI融资: AI投资、AI估值、AI IPO
- 大模型: LLM、GPT、Claude、Transformer
- AI产品: AI应用、AI工具、AI助手、AI Agent

**重要**: 使用语义匹配而非关键词精确匹配

## 核心代码文件

| 文件 | 说明 |
|------|------|
| `src/auto_push.py` | 自动推送主脚本 (唯一入口) |
| `src/llm_filter.py` | AI 筛选模块 |
| `src/wechat_pusher.py` | 企业微信推送模块 |
| `run_auto_push.sh` | 启动脚本 (加载 .env + 执行 Python) |
| `admin/app.py` | Flask 管理后台 |

## 故障排查

### 大模型 API 调用失败

检查:
1. API Key 是否正确 (`.env` 中的 `LLM_API_KEY`)
2. 网络连接是否正常
3. 请求体格式是否符合要求

### API4 获取文章失败 ("参数不对")

检查:
1. 环境变量 `API4_USER` 和 `API4_TOKEN` 是否正确加载
2. Cron 任务是否通过 `run_auto_push.sh` 执行 (确保 `.env` 被加载)
3. 详见 [CRON_SETUP.md](CRON_SETUP.md) 排查

### 企业微信推送失败

检查:
1. `WECHAT_WEBHOOK_KEY` 是否有效
2. 是否超过频率限制 (20条/秒)
3. 消息格式是否正确

## 数据流说明

1. **文章获取**: 通过今天看啥 API4 接口获取公众号文章 (JSON 格式)
2. **去重过滤**: 基于 SQLite 数据库,过滤已推送的文章 (保留30天历史)
3. **批量处理**: 每批15篇文章,避免 LLM API 超时
4. **AI 筛选**: 大模型判断文章与 AI 主题相关性,返回 JSON 格式结果
5. **结果解析**: 提取相关文章,生成分类标签和置信度
6. **消息格式化**: 使用 Markdown 格式,包含标题、分类、链接
7. **企业微信推送**: Webhook 方式发送到群聊,分批推送 (每批最多20篇)

## 重要注意事项

1. **API Key 安全**: 
   - 所有密钥通过 `.env` 文件管理
   - `.env` 已在 `.gitignore` 中,不会提交到代码库

2. **推送频率限制**:
   - 企业微信机器人: 20条/秒
   - 大模型 API: 根据供应商限制调整批次大小
   - 今天看啥 API: 并发数限制为3,请求间隔1秒

3. **Cron 环境变量**:
   - Cron 不会自动加载 `.env`,必须通过 `run_auto_push.sh` 启动
   - 详见 [CRON_SETUP.md](CRON_SETUP.md)

## 相关文档

- PRD.md - 详细产品需求文档
- requirements.md - 技术需求说明
- CRON_SETUP.md - Cron 定时任务配置指南
- AUTO_PUSH_CONFIG.md - 自动推送配置说明
- 今天看啥: https://www.jintiankansha.me/
