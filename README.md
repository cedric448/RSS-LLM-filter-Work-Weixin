# RSS 智能筛选推送系统

基于大语言模型的智能RSS内容筛选系统，自动推送AI领域资讯到企业微信。

---

## 🚀 快速开始

### 系统状态

- ✅ 已部署上线
- ✅ 自动推送运行中（每天 9:00、13:00、20:00）
- ✅ 当前订阅 4 个公众号
- ✅ Web管理后台可用

### 快速检查

```bash
# 一键健康检查
/root/check_rss_system.sh

# 查看最近推送
tail -50 /root/project-wb/n8n/logs/auto_push.log | grep "推送完成" -A 5

# 手动执行推送
cd /root/project-wb/n8n && python3 src/auto_push.py
```

---

## 📚 文档导航

### 核心文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **需求文档** | [docs/需求文档.md](docs/需求文档.md) | 完整的系统需求、架构设计、技术规格 |
| **运维手册** | [docs/运维手册.md](docs/运维手册.md) | 日常运维、监控告警、故障排查、备份恢复、去重机制 |
| **使用手册** | [docs/使用手册.md](docs/使用手册.md) | 添加公众号、调整筛选、修改推送设置 |
| **问题修复记录** | [docs/问题修复记录.md](docs/问题修复记录.md) | 历史问题记录、根因分析、修复方案、经验教训 |

### 项目配置文档

| 文档 | 说明 |
|------|------|
| [CODEBUDDY.md](CODEBUDDY.md) | CodeBuddy 开发指南 |
| [AUTO_PUSH_CONFIG.md](AUTO_PUSH_CONFIG.md) | 自动推送配置说明 |
| [PRD.md](PRD.md) | 产品需求文档（原始版本） |
| [requirements.md](requirements.md) | 技术需求文档（原始版本） |

---

## 📂 项目结构

```
/root/project-wb/n8n/
├── src/                          # 核心代码
│   ├── auto_push.py             # 自动推送主脚本 ⭐
│   ├── llm_filter.py            # AI筛选模块
│   └── wechat_pusher.py         # 企业微信推送模块
├── config/                       # 配置文件
│   ├── rss-sources.json         # RSS源配置 ⭐
│   └── keywords.json            # 筛选规则配置 ⭐
├── data/                         # 数据目录
│   └── push_history.db          # 推送历史数据库（SQLite）
├── logs/                         # 日志目录
│   └── auto_push.log            # 推送日志 ⭐
├── docs/                         # 文档目录 ⭐
│   ├── 需求文档.md
│   ├── 运维手册.md
│   ├── 使用手册.md
│   └── 问题修复记录.md          # 历史问题修复记录 🆕
├── scripts/                      # 运维脚本目录
│   ├── backup_config.sh         # 配置备份
│   ├── backup_database.sh       # 数据库备份
│   ├── check_rss_health.sh      # RSS健康检查
│   └── weekly_maintenance.sh    # 周维护脚本
├── admin/                        # Web管理后台
│   ├── app.py                   # Flask应用
│   ├── templates/               # HTML模板
│   └── start.sh                 # 启动脚本
├── archive/                      # 归档目录 ⭐
│   ├── docs/                    # 过程文档归档
│   ├── tests/                   # 测试文件归档
│   ├── workflows/               # 旧版工作流归档
│   └── README.md                # 归档说明
└── README.md                     # 本文档

⭐ = 新增/重要文件
```

---

## 🔧 常用操作

### 查看系统状态

```bash
# 查看最近推送
tail -100 /root/project-wb/n8n/logs/auto_push.log | grep "推送完成" -A 5

# 查看定时任务
crontab -l | grep auto_push

# 查看数据库大小
du -h /root/project-wb/n8n/data/push_history.db

# 查看RSS源列表
cat /root/project-wb/n8n/config/rss-sources.json | jq '.sources[] | {name, enabled}'
```

### 添加公众号

**方式1: Web管理后台**（推荐）
```
访问: https://<服务器IP>:8443
授权码: change-this-password-in-production
```

**方式2: 编辑配置文件**
```bash
vi /root/project-wb/n8n/config/rss-sources.json
```

详见 [使用手册](docs/使用手册.md#添加公众号)

### 调整筛选规则

```bash
# 编辑筛选配置
vi /root/project-wb/n8n/config/keywords.json

# 手动测试筛选效果
cd /root/project-wb/n8n && python3 src/auto_push.py
```

详见 [使用手册](docs/使用手册.md#调整筛选逻辑)

### 修改推送时间

```bash
# 编辑crontab
crontab -e

# 当前配置: 9:00, 13:00, 20:00
0 9,13,20 * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1
```

详见 [使用手册](docs/使用手册.md#调整推送设置)

---

## 🛠️ 运维操作

### 查看日志

```bash
# 查看完整日志
cat /root/project-wb/n8n/logs/auto_push.log

# 查看最新50行
tail -50 /root/project-wb/n8n/logs/auto_push.log

# 实时查看
tail -f /root/project-wb/n8n/logs/auto_push.log

# 查看今天的日志
grep "$(date +%Y-%m-%d)" /root/project-wb/n8n/logs/auto_push.log
```

### 备份与恢复

```bash
# 配置文件备份
/root/project-wb/n8n/scripts/backup_config.sh

# 数据库备份
/root/project-wb/n8n/scripts/backup_database.sh

# 完整备份
/root/project-wb/n8n/scripts/backup_full.sh
```

详见 [运维手册](docs/运维手册.md#备份与恢复)

### 故障排查

```bash
# 健康检查
/root/check_rss_system.sh

# RSS源健康检查
/root/project-wb/n8n/scripts/check_rss_health.sh

# 查看错误日志
grep "ERROR\|失败" /root/project-wb/n8n/logs/auto_push.log | tail -20
```

详见 [运维手册](docs/运维手册.md#故障排查)

---

## 📊 系统配置

### 当前订阅的公众号

1. 鞭牛士 - 科技资讯
2. 机器之心 - AI技术
3. 创业邦 - 创业投资
4. 新智元 - AI资讯

### 筛选分类

1. **AIGC / 生成式AI** - 文生图、文生视频、AI创作工具
2. **AI初创公司** - 创业动态、团队组建、产品发布
3. **AI融资投资** - 融资新闻、投资趋势、估值信息
4. **大模型技术** - LLM研究、模型发布、技术突破
5. **AI产品应用** - AI工具、AI助手、行业应用

### 推送时间

- 🌅 **09:00** - 早间推送（工作日开始）
- 🌞 **13:00** - 午间推送（午休后）
- 🌙 **20:00** - 晚间推送（下班后）

---

## 🔑 重要配置

### API密钥

- **AI模型API**: `http://your-llm-api-host/agent`
- **企业微信Webhook**: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=defd0b35...`
- **今天看啥账号**: `your-email@example.com`

⚠️ 密钥信息请妥善保管，不要泄露

### Web管理后台

- **地址**: `https://<服务器IP>:8443`
- **授权码**: `change-this-password-in-production`

---

## 📦 归档文件

项目整理时已将以下文件归档到 `archive/` 目录：

### 归档的过程文档
- E2E_TEST_REPORT.md - 端到端测试报告
- DEPLOYMENT_VERIFICATION.md - 部署验证文档
- LARGE_SCALE_TEST_REPORT.md - 大规模测试报告
- RETRY_AND_BATCH_FEATURES.md - 重试和批处理功能说明
- DEDUPLICATION.md - 去重功能说明
- DAILY_REPORT_2026-02-21.md - 每日运行报告
- jintiankansha-api.md - 旧版API文档

### 归档的测试文件
- test_batch_push.py - 批量推送测试
- test_e2e_13pm.py - 13点推送端到端测试

### 归档的备份文件
- rss-sources.json.backup - RSS源配置备份

这些文件在 `archive/` 目录中保留，以供查阅。详见 [archive/README.md](archive/README.md)

---

## 📝 文档整理完成

✅ **任务1**: 清理无用文件 - 已完成
- 过程文档已归档到 `archive/docs/`
- 测试文件已归档到 `archive/tests/`
- 备份文件已归档到 `archive/workflows/`

✅ **任务2**: 整理需求文档 - 已完成
- 创建完整的 [需求文档](docs/需求文档.md)
- 包含功能需求、技术架构、数据流程、AI筛选规则等

✅ **任务3**: 编写运维手册 - 已完成
- 创建详细的 [运维手册](docs/运维手册.md)
- 包含日常运维、监控告警、故障排查、备份恢复等

✅ **任务4**: 编写使用手册 - 已完成
- 创建易用的 [使用手册](docs/使用手册.md)
- 包含添加公众号、调整筛选、修改推送等操作指南

---

## 🔧 关键修复历史

### 2026-02-21: 批次索引映射Bug修复 🔴

**问题**: 从第2批开始,大量文章被标记为"未解析"并跳过AI筛选

**影响**:
- 未解析率: 88% (109/124篇)
- 识别率: 仅6.5% (从正常的56%下降)
- 第2批及以后的文章全部无法被AI处理

**根本原因**: 批次索引映射错误
- AI返回全局索引(16-30)
- 代码检查批次内索引(0-14)
- 导致范围检查失败,所有第2批+文章被跳过

**修复方案**:
```python
# 修复前 (错误)
idx = r.get('index', 0) - 1  # AI返回16,减1得15
if 0 <= idx < len(articles):  # 15不在0-14范围内!
    ai_judgments[idx] = r

# 修复后 (正确)
global_idx = r.get('index', 0)  # AI返回16
relative_idx = global_idx - start_index  # 16-16=0 ✅
if 0 <= relative_idx < len(articles):
    ai_judgments[relative_idx] = r
```

**修复效果**:
- ✅ 未解析率: 88% → 0%
- ✅ 识别率: 6.5% → 56.3% (+762%)
- ✅ 推送文章: 4篇 → 80篇 (+1900%)
- ✅ 批次成功率: 11% → 100%

**详细分析**: [docs/问题修复记录.md#批次索引映射bug修复](docs/问题修复记录.md#批次索引映射bug修复)

### 2026-02-21: 去重机制验证 ✅

**验证目的**: 确认已推送文章不会重复推送

**测试覆盖**:
- ✅ 哈希生成一致性
- ✅ 已推送文章查询
- ✅ 新文章过滤逻辑
- ✅ 标记推送机制
- ✅ 唯一约束测试
- ✅ 链接优先策略

**验证结果**: 
- 6个核心场景全部通过
- 数据库无重复记录(166条记录,0重复)
- 查询性能<1ms/篇
- 去重机制完全正常 ✅

**详细报告**: [docs/问题修复记录.md#去重机制验证](docs/问题修复记录.md#去重机制验证)

---

## 📞 获取帮助

**遇到问题时**:
1. 查阅相关文档（需求、运维、使用手册）
2. 运行健康检查: `/root/check_rss_system.sh`
3. 查看日志文件: `/root/project-wb/n8n/logs/auto_push.log`
4. 参考运维手册的故障排查章节

**文档位置**:
- 需求文档: `docs/需求文档.md`
- 运维手册: `docs/运维手册.md`
- 使用手册: `docs/使用手册.md`
- 问题修复记录: `docs/问题修复记录.md`

---

**最后更新**: 2026-02-21  
**项目状态**: ✅ 运行中  
**最近修复**: 批次索引映射Bug (2026-02-21)
