# RSS 智能筛选自动推送 - 配置文档

## ✅ 配置完成

已成功配置定时自动推送系统，每天在 **9:00、13:00、20:00** 自动执行 RSS 获取、AI 筛选和企业微信推送。

---

## 📋 系统配置

### 自动推送脚本

**脚本路径**: `/root/project-wb/n8n/src/auto_push.py`

**功能**:
1. 从配置文件读取 4 个公众号 RSS 源
2. 获取每个源最新的 20 篇文章（共 80 篇）
3. **过滤已推送的文章（去重机制）**
4. 使用 AI 模型筛选 AI 相关文章
5. 将筛选结果推送到企业微信群
6. **标记文章为已推送（避免重复）**

**特点**:
- ✅ 自动从 `/root/project-wb/n8n/config/rss-sources.json` 读取 RSS 源
- ✅ 只处理 `enabled: true` 的源
- ✅ **文章去重机制（每篇文章只推送一次）**
- ✅ **推送历史数据库（SQLite，保留30天）**
- ✅ 完整日志输出（包含执行时间、筛选统计、去重统计）
- ✅ 异常处理和错误恢复

### Cron 定时任务

**Crontab 配置**:
```cron
# RSS 智能筛选推送 - 每天 9:00, 13:00, 20:00
0 9,13,20 * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1
```

**执行时间**:
- 🌅 **09:00** - 早晨推送（工作日开始）
- 🌞 **13:00** - 午间推送（午休后）
- 🌙 **20:00** - 晚间推送（下班后）

**日志文件**: `/root/project-wb/n8n/logs/auto_push.log`

### RSS 源配置

**配置文件**: `/root/project-wb/n8n/config/rss-sources.json`

**当前配置的 4 个公众号**:

| ID | 公众号名称 | 状态 |
|----|-----------|------|
| source_6 | 鞭牛士 | ✅ enabled |
| source_7 | 机器之心 | ✅ enabled |
| source_8 | 创业邦 | ✅ enabled |
| source_9 | 新智元 | ✅ enabled |

**修改 RSS 源**:
1. 方式一: 使用管理后台（推荐）
   - 访问: `https://172.19.48.4:8443`
   - 登录后在 Web 界面添加/删除/启用/禁用 RSS 源

2. 方式二: 直接编辑配置文件
   - 编辑: `/root/project-wb/n8n/config/rss-sources.json`
   - 设置 `enabled: true/false` 来启用/禁用源
   - 无需重启服务，下次执行时自动生效

---

## 🔧 管理操作

### 查看定时任务

```bash
# 查看所有 crontab
crontab -l

# 查看 RSS 推送任务
crontab -l | grep auto_push
```

### 查看执行日志

```bash
# 查看完整日志
cat /root/project-wb/n8n/logs/auto_push.log

# 查看最新 50 行
tail -50 /root/project-wb/n8n/logs/auto_push.log

# 实时查看日志
tail -f /root/project-wb/n8n/logs/auto_push.log
```

### 手动执行推送

```bash
# 进入项目目录
cd /root/project-wb/n8n

# 手动运行（查看详细输出）
python3 src/auto_push.py

# 后台运行（输出到日志）
python3 src/auto_push.py >> logs/auto_push.log 2>&1 &
```

### 测试 RSS 源

```bash
# 测试单个 RSS 源
curl -s "http://rss.jintiankansha.me/rss/..." | head -100

# 测试所有 RSS 源可访问性
python3 -c "
import json
import requests
with open('config/rss-sources.json', 'r') as f:
    sources = json.load(f)['sources']
for s in sources:
    try:
        r = requests.get(s['url'], timeout=10)
        print(f'✓ {s[\"name\"]}: {r.status_code}')
    except Exception as e:
        print(f'✗ {s[\"name\"]}: {e}')
"
```

### 修改推送时间

编辑 crontab:
```bash
crontab -e
```

修改这一行:
```cron
# 原配置: 9:00, 13:00, 20:00
0 9,13,20 * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1

# 示例: 改为 8:00, 12:00, 18:00, 22:00
0 8,12,18,22 * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1

# 示例: 改为每小时执行
0 * * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1
```

### 暂停/恢复自动推送

```bash
# 暂停: 注释掉 crontab 行
crontab -e
# 在任务行前加 #

# 恢复: 取消注释
crontab -e
# 删除任务行前的 #

# 或者临时禁用所有 RSS 源
# 编辑 config/rss-sources.json，设置所有 enabled: false
```

---

## 📊 监控与统计

### 日志格式

每次执行的日志包含:
```
============================================================
🚀 RSS 智能筛选自动推送
   开始时间: 2026-02-20 09:00:01
============================================================

📥 步骤 1: 获取 RSS 源列表
✓ 读取到 4 个启用的 RSS 源

📰 步骤 2: 获取文章 (每源最多 20 篇)
  ✓ 鞭牛士: 20 篇文章
  ✓ 机器之心: 20 篇文章
  ✓ 创业邦: 20 篇文章
  ✓ 新智元: 20 篇文章
  
  总计: 80 篇文章

🤖 步骤 3: AI 智能筛选
  ✓ 筛选结果: 15/80 篇文章符合条件
  
  📊 筛选文章:
    1. [机器之心] OpenAI发布新模型... [大模型 | AI产品]
    2. [新智元] 字节AI视频工具上线... [AIGC | AI产品]
    ...

📤 步骤 4: 推送到企业微信
  ✓ 推送成功: 15 篇文章

============================================================
✅ 推送完成
   结束时间: 2026-02-20 09:00:45
   耗时: 44.2 秒
   输入: 80 篇
   筛选: 15 篇 (18.8%)
   推送: 15 篇
============================================================
```

### 统计脚本

查看最近 10 次执行统计:
```bash
grep "推送完成" /root/project-wb/n8n/logs/auto_push.log -A 5 | tail -60
```

查看今天的推送记录:
```bash
TODAY=$(date +%Y-%m-%d)
grep "$TODAY" /root/project-wb/n8n/logs/auto_push.log | grep "推送完成" -A 5
```

---

## ⚠️ 故障排查

### 问题 1: 定时任务未执行

**检查**:
```bash
# 1. 确认 crontab 已配置
crontab -l | grep auto_push

# 2. 检查 crond 服务运行
systemctl status crond

# 3. 查看系统日志
grep CRON /var/log/cron | tail -20
```

**解决**:
```bash
# 重启 crond 服务
systemctl restart crond

# 确保脚本有执行权限
chmod +x /root/project-wb/n8n/src/auto_push.py
```

### 问题 2: 推送失败

**检查**:
```bash
# 查看最新日志
tail -100 /root/project-wb/n8n/logs/auto_push.log

# 手动执行查看详细错误
cd /root/project-wb/n8n && python3 src/auto_push.py
```

**常见原因**:
- RSS 源无法访问（网络问题）
- AI API 调用失败（API Key 或配额）
- 企业微信 Webhook 失效

### 问题 3: RSS 源获取失败

**检查**:
```bash
# 测试 RSS 源可访问性
curl -I "http://rss.jintiankansha.me/rss/..."

# 查看配置文件
cat /root/project-wb/n8n/config/rss-sources.json
```

**解决**:
- 更新 RSS 源 URL
- 检查网络连接
- 暂时禁用失败的源（设置 `enabled: false`）

### 问题 4: 日志文件过大

**清理日志**:
```bash
# 查看日志大小
du -h /root/project-wb/n8n/logs/auto_push.log

# 备份并清空日志
mv /root/project-wb/n8n/logs/auto_push.log /root/project-wb/n8n/logs/auto_push.log.$(date +%Y%m%d)
touch /root/project-wb/n8n/logs/auto_push.log

# 或使用 logrotate 自动管理
```

---

## 🔄 更新与维护

### 更新 RSS 源列表

**方式一: 使用管理后台**（推荐）
1. 访问 `https://172.19.48.4:8443`
2. 登录（授权码: `change-this-password-in-production`）
3. 添加/删除/修改 RSS 源
4. 保存后自动生效

**方式二: 手动编辑**
```bash
# 编辑配置
vi /root/project-wb/n8n/config/rss-sources.json

# 验证 JSON 格式
python3 -m json.tool /root/project-wb/n8n/config/rss-sources.json

# 无需重启，下次执行自动生效
```

### 更新脚本代码

```bash
# 编辑脚本
vi /root/project-wb/n8n/src/auto_push.py

# 测试修改
cd /root/project-wb/n8n && python3 src/auto_push.py

# 无需重启 cron，下次执行自动使用新代码
```

### 升级 AI 模型或 API

修改 `/root/project-wb/n8n/src/llm_filter.py` 中的 API 配置:
```python
# LLM API 配置
API_URL = "http://your-llm-api-host/agent"
API_KEY = "your-api-key"
MODEL_NAME = "kimi-k2.5-ioa"
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [E2E_TEST_REPORT.md](E2E_TEST_REPORT.md) | 端到端测试报告 |
| [DEPLOYMENT_COMPLETE.md](admin/DEPLOYMENT_COMPLETE.md) | 生产环境部署文档 |
| [CODEBUDDY.md](CODEBUDDY.md) | 项目开发指南 |
| [PRD.md](PRD.md) | 产品需求文档 |

---

## 📞 支持

### 快速命令

```bash
# 查看下次执行时间
crontab -l | grep auto_push

# 查看最近执行结果
tail -50 /root/project-wb/n8n/logs/auto_push.log

# 立即执行推送
cd /root/project-wb/n8n && python3 src/auto_push.py

# 查看 RSS 源配置
cat /root/project-wb/n8n/config/rss-sources.json

# 访问管理后台
# https://172.19.48.4:8443
```

### 监控建议

建议配置以下监控:
1. **Cron 执行监控**: 检查定时任务是否按时执行
2. **推送成功率监控**: 统计每天成功推送的次数
3. **RSS 源健康检查**: 定期检查 RSS 源可访问性
4. **日志大小监控**: 防止日志文件占用过多磁盘空间

---

**配置完成时间**: 2026-02-20 21:52  
**自动推送状态**: ✅ 已启用  
**下次执行时间**: 根据当前时间自动计算（9:00/13:00/20:00）
