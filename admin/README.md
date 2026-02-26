# RSS 源管理后台

用于管理"今天看点啥"公众号 RSS 订阅源的 Web 后台系统。

## 功能特性

✅ **安全鉴权**
- 基于 AUTH_CODE 的登录认证
- Session 持久化（24 小时有效期）
- 未授权自动跳转登录页
- 安全退出登录功能

✅ **RSS 源管理**
- 添加新的公众号 RSS 订阅
- 编辑现有订阅信息
- 删除不需要的订阅
- 启用/禁用特定订阅

✅ **直观界面**
- 简洁美观的 Web 界面
- 实时查看所有订阅状态
- 快速操作按钮

✅ **配置持久化**
- 自动保存到 JSON 配置文件
- 与主推送系统共享配置

## 快速开始

### 1. 配置授权码

复制环境变量配置文件：

```bash
cd /root/project-wb/n8n/admin
cp .env.example .env
```

编辑 `.env` 文件，修改授权码：

```bash
# 使用你自己的强密码
RSS_ADMIN_AUTH_CODE=your-secure-password-here
```

**安全建议**：
- 使用至少 20 个字符的随机字符串
- 包含大小写字母、数字和特殊字符
- 不要使用常见密码或个人信息
- 定期更换授权码

**生成随机授权码**：
```bash
# Linux/Mac
openssl rand -base64 32

# 或使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 启动后台

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接运行
python3 app.py
```

### 4. 访问后台

1. 打开浏览器访问: **http://localhost:5002**
2. 输入配置的授权码登录
3. 登录成功后即可管理 RSS 源

## 安全配置

### 授权码配置

授权码通过环境变量 `RSS_ADMIN_AUTH_CODE` 配置，优先级：

1. 系统环境变量
2. `.env` 文件
3. 默认值（不推荐使用）

**设置系统环境变量**：
```bash
# Linux/Mac
export RSS_ADMIN_AUTH_CODE="your-secure-password"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export RSS_ADMIN_AUTH_CODE="your-secure-password"' >> ~/.bashrc
source ~/.bashrc
```

### Session 配置

- **有效期**: 24 小时
- **存储方式**: Flask Session（服务器端）
- **自动过期**: 超时后需重新登录

### 访问控制

所有 API 端点和管理页面都需要登录才能访问：
- ✅ `/login` - 登录页面（公开）
- ✅ `/health` - 健康检查（公开）
- 🔒 `/` - 主页（需要登录）
- 🔒 `/api/sources` - RSS 源管理（需要登录）

## 使用说明

### 登录后台

1. 访问 http://localhost:5002
2. 自动跳转到登录页
3. 输入授权码
4. 点击"登录"按钮

### 退出登录

点击页面右上角的 **"🚪 退出登录"** 按钮

### 其他操作

登录后的操作与之前相同，详见 [USAGE.md](USAGE.md)

## 使用说明

### 添加 RSS 源

1. 点击"➕ 添加 RSS 源"按钮
2. 填写公众号名称（必填）
3. 填写 RSS 链接（必填）
   - 格式：`http://rss.jintiankansha.me/rss/YOUR_RSS_CODE`
4. 填写描述（可选）
5. 点击"保存"

### 获取"今天看点啥" RSS 链接

1. 访问 https://www.jintiankansha.me/
2. 登录账号
3. 进入"我的订阅"
4. 找到想要订阅的公众号
5. 复制对应的 RSS 链接

### 编辑 RSS 源

1. 在列表中找到要编辑的源
2. 点击"编辑"按钮
3. 修改信息后点击"保存"

### 启用/禁用 RSS 源

1. 点击"启用"或"禁用"按钮
2. 禁用的源不会被推送系统获取

### 删除 RSS 源

1. 点击"删除"按钮
2. 确认删除操作

## 配置文件

配置保存在: `/root/project-wb/n8n/config/rss-sources.json`

格式示例:
```json
{
  "sources": [
    {
      "id": "source_1",
      "name": "机器之心",
      "url": "http://rss.jintiankansha.me/rss/...",
      "description": "AI 行业资讯",
      "enabled": true,
      "created_at": "2026-02-20T20:00:00"
    }
  ],
  "total": 1,
  "updated_at": "2026-02-20T20:00:00"
}
```

## API 接口

### 获取所有源
```
GET /api/sources
```

### 添加源
```
POST /api/sources
Content-Type: application/json

{
  "name": "公众号名称",
  "url": "RSS链接",
  "description": "描述"
}
```

### 更新源
```
PUT /api/sources/{source_id}
Content-Type: application/json

{
  "name": "新名称",
  "url": "新链接"
}
```

### 删除源
```
DELETE /api/sources/{source_id}
```

### 启用/禁用源
```
POST /api/sources/{source_id}/toggle
```

## 注意事项

1. **端口占用**: 默认使用 5002 端口，如有冲突请修改 `app.py` 中的端口配置
2. **权限问题**: 确保对配置文件目录有写入权限
3. **RSS 链接**: 必须是有效的"今天看点啥" RSS 链接
4. **配置同步**: 修改后立即生效，主推送系统会使用最新配置

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML + CSS + JavaScript (原生)
- **存储**: JSON 文件

## 故障排查

### 端口被占用
```bash
# 查找占用端口的进程
lsof -ti:5002 | xargs kill -9

# 或修改 app.py 使用其他端口
```

### 配置保存失败
```bash
# 检查目录权限
ls -la /root/project-wb/n8n/config/

# 创建配置目录
mkdir -p /root/project-wb/n8n/config/
```

### 依赖安装失败
```bash
# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 相关文档

- 主推送系统: `/root/project-wb/n8n/src/main.py`
- 配置文件: `/root/project-wb/n8n/config/rss-sources.json`
- 今天看点啥: https://www.jintiankansha.me/
