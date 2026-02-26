# 归档文件说明

本目录存放项目开发过程中产生的临时文档、测试文件和备份文件。这些文件在日常运维中不需要使用，但保留以供查阅。

## 目录结构

### docs/ - 过程文档
- `E2E_TEST_REPORT.md` - 端到端测试报告
- `DEPLOYMENT_VERIFICATION.md` - 部署验证文档
- `LARGE_SCALE_TEST_REPORT.md` - 大规模测试报告
- `RETRY_AND_BATCH_FEATURES.md` - 重试和批处理功能说明
- `DEDUPLICATION.md` - 去重功能说明
- `DAILY_REPORT_2026-02-21.md` - 每日运行报告
- `jintiankansha-api.md` - 旧版API文档

### tests/ - 测试脚本
- `test_batch_push.py` - 批量推送测试
- `test_e2e_13pm.py` - 13点推送端到端测试

### workflows/ - 备份文件
- `rss-ai-filter-workflow.backup.json` - n8n工作流备份
- `rss-sources.json.backup` - RSS源配置备份

### 根目录
- `docker-compose-simple.yml` - 简化版docker配置（已弃用）

## 何时查阅归档文件

- 需要了解功能实现细节时
- 排查历史问题时
- 参考测试方法时
- 恢复旧版配置时

## 清理策略

归档文件会保留至少6个月，超过时间后可以安全删除。
