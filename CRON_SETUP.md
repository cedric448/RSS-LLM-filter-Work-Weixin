# Cron 定时任务配置指南

## 问题说明

Cron 任务执行时**不会自动加载** `.env` 文件中的环境变量,这会导致 Python 脚本中的 `os.environ.get()` 无法获取配置,从而引发 API 调用失败。

### 典型错误表现

```
✗ 鞭牛士: API返回错误 - 参数不对
✗ 创业邦: API返回错误 - 参数不对
...
总计: 0 篇文章
成功: 0 个源
失败: 43 个源
```

**原因**: `API4_USER` 和 `API4_TOKEN` 环境变量为空,导致 API 请求缺少必需参数。

---

## 解决方案

### 方案 1: 使用启动脚本 (推荐) ✅

创建 `run_auto_push.sh` 脚本,在执行 Python 脚本前加载环境变量:

```bash
#!/bin/bash
# RSS 自动推送脚本 - 加载环境变量并执行

# 切换到项目目录
cd /root/project-wb/n8n

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 执行推送脚本
/usr/bin/python3 src/auto_push.py
```

**配置 Crontab**:
```bash
# 编辑 crontab
crontab -e

# 添加定时任务 (每天 9:05, 13:05, 20:05)
5 9,13,20 * * * /root/project-wb/n8n/run_auto_push.sh >> /root/project-wb/n8n/logs/auto_push.log 2>&1
```

---

### 方案 2: 在 Crontab 中直接设置环境变量

```bash
crontab -e
```

添加:
```bash
# 环境变量
API4_USER=your-email@example.com
API4_TOKEN=your-api-token
LLM_API_URL=http://your-llm-endpoint
LLM_API_KEY="Bearer your-api-key"
WECHAT_WEBHOOK_KEY=your-webhook-key

# 定时任务
5 9,13,20 * * * cd /root/project-wb/n8n && /usr/bin/python3 src/auto_push.py >> logs/auto_push.log 2>&1
```

**缺点**: 
- 敏感信息直接暴露在 crontab 中
- 难以维护和更新
- 不推荐用于生产环境

---

### 方案 3: 使用系统级环境变量

将环境变量添加到 `/etc/environment`:

```bash
sudo vim /etc/environment
```

添加:
```
API4_USER="your-email@example.com"
API4_TOKEN="your-api-token"
LLM_API_URL="http://your-llm-endpoint"
LLM_API_KEY="Bearer your-api-key"
WECHAT_WEBHOOK_KEY="your-webhook-key"
```

**注意**: 需要重启系统或重新登录才能生效。

---

## 验证配置

### 1. 测试环境变量加载

```bash
cd /root/project-wb/n8n

# 测试 .env 加载
bash -c 'source .env && echo "API4_USER=$API4_USER"'
```

### 2. 手动执行脚本

```bash
# 使用启动脚本
/root/project-wb/n8n/run_auto_push.sh
```

### 3. 查看日志验证

```bash
# 查看最新日志
tail -100 /root/project-wb/n8n/logs/auto_push.log

# 检查是否有"参数不对"错误
grep "参数不对" /root/project-wb/n8n/logs/auto_push.log
```

### 4. 测试 Cron 任务

```bash
# 手动触发 cron 任务 (以 root 用户运行)
/root/project-wb/n8n/run_auto_push.sh >> /root/project-wb/n8n/logs/auto_push.log 2>&1

# 查看执行结果
tail -50 /root/project-wb/n8n/logs/auto_push.log
```

---

## 常见问题

### Q1: 如何查看当前的 crontab 配置?

```bash
crontab -l
```

### Q2: 如何查看 cron 任务执行历史?

```bash
# 查看系统日志
grep CRON /var/log/syslog | tail -20

# 或查看应用日志
tail -100 /root/project-wb/n8n/logs/auto_push.log
```

### Q3: 为什么 crontab 不能直接读取 .env?

Cron 任务在非交互式 shell 中运行,不会加载用户的配置文件(如 `.bashrc`, `.profile`),也不会自动读取项目目录下的 `.env` 文件。必须显式地在脚本中加载环境变量。

### Q4: 如何确认 cron 任务正在运行?

```bash
# 查看 cron 服务状态
systemctl status cron

# 查看最近的 cron 执行记录
grep "auto_push" /var/log/syslog | tail -10
```

### Q5: 修改 .env 后需要重启 cron 吗?

不需要。`.env` 文件在每次任务执行时都会重新加载。但如果修改了 `run_auto_push.sh` 脚本本身,需要确保文件有执行权限:

```bash
chmod +x /root/project-wb/n8n/run_auto_push.sh
```

---

## 推荐的最佳实践

1. ✅ **使用启动脚本** (`run_auto_push.sh`) - 安全、灵活、易维护
2. ✅ **将 `.env` 加入 `.gitignore`** - 防止敏感信息泄露
3. ✅ **定期检查日志** - 及时发现问题
4. ✅ **设置日志轮转** - 防止日志文件过大
5. ✅ **使用绝对路径** - Cron 任务中避免使用相对路径

---

## 相关文件

- `.env` - 环境变量配置文件 (不提交到 Git)
- `.env.example` - 环境变量模板
- `run_auto_push.sh` - 启动脚本 (包含环境变量加载)
- `SETUP.md` - 环境配置详细指南
- `logs/auto_push.log` - 执行日志

---

## 更新记录

- **2026-03-01**: 创建文档,添加 `run_auto_push.sh` 脚本解决 cron 环境变量问题
- **2026-02-28**: 发现问题 - cron 任务无法读取 .env 导致推送失败
