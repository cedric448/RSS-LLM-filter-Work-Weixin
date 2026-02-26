# RSS 源管理后台使用指南

## 快速开始

### 1. 启动服务

```bash
cd /root/project-wb/n8n/admin
./start.sh
```

### 2. 访问后台

浏览器打开: **http://localhost:5002**

![后台界面预览](https://via.placeholder.com/800x400/667eea/ffffff?text=RSS+管理后台)

## 功能说明

### 📋 查看 RSS 源列表

- 显示所有已配置的公众号 RSS 源
- 查看每个源的状态（已启用/已禁用）
- 显示公众号名称、RSS 链接、描述信息

### ➕ 添加 RSS 源

1. 点击页面顶部的 **"➕ 添加 RSS 源"** 按钮
2. 在弹出的表单中填写信息：
   - **公众号名称**: 例如 "机器之心"、"量子位" 等
   - **RSS 链接**: 从"今天看点啥"获取的 RSS 订阅链接
   - **描述**: （可选）简单描述该公众号的内容特点
3. 点击 **"保存"** 按钮

**示例**:
- 公众号名称: `机器之心`
- RSS 链接: `http://rss.jintiankansha.me/rss/G42TC7BZGQ2GCNZRMVSGCZBSGY2GCM3BMI2DKNTEG43GCNTBGVSDQZDBGJQTMNZSGA4WGNI=`
- 描述: `AI 行业资讯与技术深度报道`

### ✏️ 编辑 RSS 源

1. 在列表中找到要编辑的源
2. 点击右侧的 **"编辑"** 按钮
3. 修改信息后点击 **"保存"**

### 🔄 启用/禁用 RSS 源

- 点击 **"启用"** 或 **"禁用"** 按钮
- 禁用的源会显示灰色，并且不会被推送系统抓取
- 临时不想接收某个公众号的推送时可以禁用

### 🗑️ 删除 RSS 源

1. 点击右侧的 **"删除"** 按钮
2. 在确认对话框中点击 **"确定"**
3. 删除后无法恢复，请谨慎操作

## 如何获取"今天看点啥" RSS 链接

### 方法一：通过官网获取

1. 访问 [今天看点啥](https://www.jintiankansha.me/)
2. 注册/登录账号
3. 搜索想要订阅的公众号
4. 点击公众号进入详情页
5. 复制页面上的 RSS 订阅链接

### 方法二：通过订阅列表获取

1. 登录"今天看点啥"
2. 进入 **"我的订阅"** 页面
3. 找到已订阅的公众号
4. 点击 RSS 图标获取链接

### RSS 链接格式

标准格式: `http://rss.jintiankansha.me/rss/[加密字符串]`

示例:
```
http://rss.jintiankansha.me/rss/G42TC7BZGQ2GCNZRMVSGCZBSGY2GCM3BMI2DKNTEG43GCNTBGVSDQZDBGJQTMNZSGA4WGNI=
```

## 配置说明

### 配置文件位置

`/root/project-wb/n8n/config/rss-sources.json`

### 配置文件结构

```json
{
  "sources": [
    {
      "id": "source_1",
      "name": "机器之心",
      "url": "http://rss.jintiankansha.me/rss/...",
      "description": "AI 行业资讯",
      "enabled": true,
      "created_at": "2026-02-20T20:00:00",
      "updated_at": "2026-02-20T20:30:00"
    }
  ],
  "total": 1,
  "updated_at": "2026-02-20T20:30:00"
}
```

### 字段说明

- `id`: 唯一标识符（自动生成）
- `name`: 公众号名称
- `url`: RSS 订阅链接
- `description`: 描述信息（可选）
- `enabled`: 是否启用（true/false）
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 与主系统集成

### 配置同步

后台修改的配置会**立即保存**到 `config/rss-sources.json`，主推送系统会自动读取最新配置。

### 推送系统读取配置

主推送系统 (`src/main.py`) 在运行时会读取配置文件中**已启用**的 RSS 源。

**修改流程**:
1. 在后台添加/修改 RSS 源
2. 配置立即保存到 JSON 文件
3. 下次推送任务运行时自动使用新配置

### 验证配置

```bash
# 查看当前配置
cat /root/project-wb/n8n/config/rss-sources.json | python3 -m json.tool

# 测试 RSS 抓取
cd /root/project-wb/n8n
python3 src/main.py
```

## 常见问题

### Q1: RSS 链接无效怎么办？

**A**: 
1. 检查链接格式是否正确
2. 确认"今天看点啥"账号是否已订阅该公众号
3. 尝试在浏览器中直接访问 RSS 链接
4. 检查公众号是否还在更新

### Q2: 配置保存失败？

**A**:
1. 检查文件权限: `ls -la /root/project-wb/n8n/config/`
2. 确保配置目录存在: `mkdir -p /root/project-wb/n8n/config/`
3. 查看后台日志: 终端会显示错误信息

### Q3: 禁用的源还在推送？

**A**:
- 禁用只影响**下一次**推送任务
- 如果任务正在运行，需要等当前任务完成
- 验证配置: 检查 JSON 文件中 `enabled` 字段是否为 `false`

### Q4: 如何批量导入 RSS 源？

**A**:
直接编辑配置文件:
```bash
vim /root/project-wb/n8n/config/rss-sources.json
```

或使用 API:
```bash
curl -X POST http://localhost:5002/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "公众号名称",
    "url": "RSS链接",
    "description": "描述"
  }'
```

### Q5: 后台端口冲突怎么办？

**A**:
修改 `admin/app.py` 文件最后一行:
```python
app.run(host='0.0.0.0', port=5003, debug=True)  # 改为其他端口
```

## 最佳实践

### 1. 合理命名

使用清晰的公众号名称，方便管理:
```
✅ 好的命名: "机器之心", "AI科技评论", "量子位"
❌ 不好的命名: "test1", "aaa", "未命名"
```

### 2. 添加描述

为每个源添加描述，说明内容特点:
```
✅ "AI 行业资讯与技术深度报道"
✅ "AI 创业公司动态与投融资消息"
❌ 留空或 "无"
```

### 3. 定期清理

- 删除长期不更新的公众号
- 禁用临时不需要的源
- 保持列表精简高效

### 4. 测试新源

添加新源后，建议:
1. 手动运行一次推送测试
2. 检查是否能正常抓取文章
3. 验证 AI 筛选结果是否符合预期

## 技术支持

- 项目仓库: `/root/project-wb/n8n/`
- 配置文件: `/root/project-wb/n8n/config/rss-sources.json`
- 主推送系统: `/root/project-wb/n8n/src/main.py`
- 后台代码: `/root/project-wb/n8n/admin/app.py`

如有问题，请查看:
1. 后台服务日志
2. 配置文件内容
3. 主推送系统运行日志
