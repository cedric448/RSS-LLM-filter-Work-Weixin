# RSS 文章去重机制说明

## ✅ 功能概述

自动推送脚本已集成文章去重机制，确保：
- ✅ 每篇文章只推送一次
- ✅ 9点推送昨晚20点到今早9点之间的新文章
- ✅ 13点推送早9点到中午13点之间的新文章
- ✅ 20点推送中午13点到晚20点之间的新文章
- ✅ 已推送的文章自动过滤，不会重复推送

---

## 🔍 去重原理

### 文章唯一标识

每篇文章通过以下方式生成唯一哈希:
```python
# 优先使用文章链接
article_hash = md5(article_link)

# 如果没有链接，使用标题+来源
article_hash = md5(f"{title}_{source_name}")
```

### 推送历史数据库

**数据库位置**: `/root/project-wb/n8n/data/push_history.db`

**表结构**:
```sql
CREATE TABLE push_history (
    id INTEGER PRIMARY KEY,
    article_hash TEXT UNIQUE,      -- 文章唯一哈希
    title TEXT,                    -- 文章标题（截取前200字符）
    link TEXT,                     -- 文章链接
    source_name TEXT,              -- 来源公众号
    push_time TIMESTAMP            -- 推送时间
);
```

**索引**:
- `idx_article_hash`: 快速查找文章是否已推送
- `idx_push_time`: 按时间范围查询历史

---

## 📊 工作流程

```
1. 获取 RSS 文章 (80篇)
   ↓
2. 查询推送历史数据库
   ↓
3. 过滤已推送文章 (假设20篇重复)
   ↓
4. 剩余新文章 (60篇)
   ↓
5. AI 筛选相关文章 (假设15篇)
   ↓
6. 推送到企业微信 (15篇)
   ↓
7. 标记为已推送 (写入数据库)
```

---

## 🧪 测试验证

### 测试场景

**第一次执行**:
```
获取: 20 篇文章
新文章: 20 篇 (100%)
AI 筛选: 11 篇
推送: 11 篇 ✅
```

**第二次执行（立即重复）**:
```
获取: 20 篇文章
过滤掉: 11 篇已推送 ✅
新文章: 9 篇 (45%)
AI 筛选: 5 篇
推送: 5 篇 ✅
```

### 验证结果

✅ **去重成功**: 第二次执行正确过滤了已推送的 11 篇文章  
✅ **数据完整**: 数据库记录了 16 篇已推送文章  
✅ **统计准确**: 推送统计信息正确显示

---

## 📈 推送统计

### 查看统计信息

脚本每次执行时自动显示:
```
📊 推送统计:
   历史总推送: 16 篇
   今日已推送: 16 篇
   最近推送: 2026-02-20 14:02:57
```

### 按来源统计

```bash
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "SELECT source_name, COUNT(*) as count FROM push_history GROUP BY source_name"
```

输出示例:
```
创业邦|3
新智元|5
机器之心|5
鞭牛士|3
```

### 按日期统计

```bash
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "SELECT DATE(push_time) as date, COUNT(*) as count FROM push_history GROUP BY DATE(push_time)"
```

### 查看最近推送

```bash
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "SELECT source_name, title, push_time FROM push_history ORDER BY push_time DESC LIMIT 10"
```

---

## 🗑️ 历史清理

### 自动清理

脚本每次执行时自动清理超过 **30 天** 的历史记录:
```python
HISTORY_RETENTION_DAYS = 30  # 保留30天
```

清理日志示例:
```
🗑️ 清理了 150 条超过 30 天的历史记录
```

### 手动清理

**清理所有历史**:
```bash
rm /root/project-wb/n8n/data/push_history.db
# 下次执行时会自动重建数据库
```

**清理特定时间前的记录**:
```bash
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "DELETE FROM push_history WHERE push_time < '2026-01-01'"
```

**清理特定来源的记录**:
```bash
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "DELETE FROM push_history WHERE source_name = '某公众号'"
```

---

## 🔧 高级配置

### 调整保留天数

编辑 `/root/project-wb/n8n/src/auto_push.py`:
```python
# 原配置: 保留 30 天
HISTORY_RETENTION_DAYS = 30

# 修改为 7 天（每周清理）
HISTORY_RETENTION_DAYS = 7

# 修改为 90 天（每季度清理）
HISTORY_RETENTION_DAYS = 90
```

### 调整每源获取数量

```python
# 原配置: 每源 20 篇
MAX_ARTICLES_PER_SOURCE = 20

# 修改为每源 50 篇（获取更多文章）
MAX_ARTICLES_PER_SOURCE = 50

# 修改为每源 10 篇（减少获取量）
MAX_ARTICLES_PER_SOURCE = 10
```

---

## 🐛 故障排查

### 问题 1: 重复推送相同文章

**原因**: 
- 数据库文件损坏
- 文章链接改变（RSS 源更新了链接格式）

**解决**:
```bash
# 检查数据库
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "SELECT COUNT(*) FROM push_history"

# 如果数据库损坏，重建
rm /root/project-wb/n8n/data/push_history.db

# 或修复数据库
sqlite3 /root/project-wb/n8n/data/push_history.db "VACUUM"
```

### 问题 2: 数据库文件过大

**检查大小**:
```bash
du -h /root/project-wb/n8n/data/push_history.db
```

**解决**:
```bash
# 减少保留天数（编辑脚本）
HISTORY_RETENTION_DAYS = 7

# 或手动清理旧记录
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "DELETE FROM push_history WHERE push_time < date('now', '-7 days')"

# 压缩数据库
sqlite3 /root/project-wb/n8n/data/push_history.db "VACUUM"
```

### 问题 3: 某些文章应该重新推送

**场景**: 文章内容更新，希望重新推送

**解决**:
```bash
# 删除特定文章的历史记录
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "DELETE FROM push_history WHERE title LIKE '%关键词%'"

# 或删除特定来源的所有记录
sqlite3 /root/project-wb/n8n/data/push_history.db \
  "DELETE FROM push_history WHERE source_name = '某公众号'"
```

---

## 📊 监控建议

### 定期检查

**每周检查**:
1. 数据库大小是否合理（通常 < 10MB）
2. 去重是否正常工作（无重复推送）
3. 历史清理是否正常执行

**监控脚本**:
```bash
#!/bin/bash
# 检查推送历史健康状态

DB_FILE="/root/project-wb/n8n/data/push_history.db"

echo "推送历史健康检查"
echo "=================="

# 数据库大小
DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
echo "数据库大小: $DB_SIZE"

# 总记录数
TOTAL=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM push_history")
echo "总记录数: $TOTAL"

# 今日推送
TODAY=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM push_history WHERE DATE(push_time) = DATE('now')")
echo "今日推送: $TODAY"

# 7天内推送
WEEK=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM push_history WHERE push_time >= datetime('now', '-7 days')")
echo "7天内推送: $WEEK"

# 最近推送时间
LAST=$(sqlite3 "$DB_FILE" "SELECT MAX(push_time) FROM push_history")
echo "最近推送: $LAST"
```

---

## 📝 日志示例

### 正常执行（有去重）

```
============================================================
🚀 RSS 智能筛选自动推送
   开始时间: 2026-02-20 09:00:01
============================================================

📊 推送统计:
   历史总推送: 45 篇
   今日已推送: 10 篇
   最近推送: 2026-02-20 08:00:15

📥 步骤 1: 获取 RSS 源列表
✓ 读取到 4 个启用的 RSS 源

📰 步骤 2: 获取文章 (每源最多 20 篇)
  ✓ 鞭牛士: 20 篇文章
  ✓ 机器之心: 20 篇文章
  ✓ 创业邦: 20 篇文章
  ✓ 新智元: 20 篇文章
  
  总计: 80 篇文章

🔍 步骤 3: 过滤重复文章
  ℹ️ 过滤掉 25 篇已推送的文章  ← 去重生效
  ✓ 新文章: 55/80 篇

🤖 步骤 4: AI 智能筛选
  ✓ 筛选结果: 12/55 篇文章符合条件

📤 步骤 5: 推送到企业微信
  ✓ 推送成功: 12 篇文章
  ✓ 已标记为已推送

============================================================
✅ 推送完成
   耗时: 45.3 秒
   获取: 80 篇
   新文章: 55 篇 (68.8%)  ← 去重后比例
   筛选: 12 篇 (21.8%)
   推送: 12 篇
============================================================
```

### 无新文章（全部重复）

```
============================================================
🚀 RSS 智能筛选自动推送
   开始时间: 2026-02-20 09:05:00
============================================================

📊 推送统计:
   历史总推送: 57 篇
   今日已推送: 22 篇
   最近推送: 2026-02-20 09:00:45

📥 步骤 1: 获取 RSS 源列表
✓ 读取到 4 个启用的 RSS 源

📰 步骤 2: 获取文章 (每源最多 20 篇)
  ✓ 鞭牛士: 20 篇文章
  ✓ 机器之心: 20 篇文章
  ✓ 创业邦: 20 篇文章
  ✓ 新智元: 20 篇文章
  
  总计: 80 篇文章

🔍 步骤 3: 过滤重复文章
  ℹ️ 过滤掉 80 篇已推送的文章  ← 全部重复
  ✓ 新文章: 0/80 篇

  ℹ️ 没有新文章，无需推送  ← 跳过后续步骤

============================================================
✅ 推送完成
   耗时: 2.1 秒
   获取: 80 篇
   新文章: 0 篇 (0.0%)
   筛选: 0 篇
   推送: 0 篇
============================================================
```

---

## ✅ 总结

### 去重机制优势

| 优势 | 说明 |
|------|------|
| ✅ **避免重复** | 每篇文章只推送一次，不骚扰用户 |
| ✅ **节省资源** | 跳过已推送文章，减少 AI 筛选成本 |
| ✅ **时间分段** | 9点/13点/20点推送各自时间段的新内容 |
| ✅ **统计完整** | 记录所有推送历史，可追溯查询 |
| ✅ **自动清理** | 30天自动清理，防止数据库膨胀 |

### 推送时间段

| 时间 | 推送内容 |
|------|----------|
| 09:00 | 昨晚 20:00 → 今早 09:00 的新文章 |
| 13:00 | 早上 09:00 → 中午 13:00 的新文章 |
| 20:00 | 中午 13:00 → 晚上 20:00 的新文章 |

---

**文档更新时间**: 2026-02-20 22:05  
**去重机制版本**: v1.0  
**测试状态**: ✅ 已验证
