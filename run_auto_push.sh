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
