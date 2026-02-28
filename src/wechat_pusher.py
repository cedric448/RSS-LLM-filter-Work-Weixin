#!/usr/bin/env python3
"""
企业微信推送模块
通过 Webhook 机器人推送消息到企业微信群
支持自动分批、消息格式化、限流处理
"""
import os
import requests
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# 配置
WECHAT_WEBHOOK_KEY = os.environ.get('WECHAT_WEBHOOK_KEY', 'your-webhook-key-here')
WECHAT_WEBHOOK = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECHAT_WEBHOOK_KEY}"
MAX_ARTICLES_PER_BATCH = 20  # 单批最大推送文章数(超过自动分批)
BATCH_INTERVAL = 2  # 批次间延迟(秒)
REQUEST_TIMEOUT = 10  # 请求超时(秒)
MAX_TITLE_LENGTH = 128  # 标题最大长度
MAX_MESSAGE_BYTES = 4000  # 单条消息最大字节数(企业微信限制 4096,留些余量)


def send_markdown(content: str) -> bool:
    """
    发送 Markdown 消息到企业微信
    
    Args:
        content: Markdown 格式的内容
    
    Returns:
        是否推送成功
    """
    if not WECHAT_WEBHOOK:
        print("  ✗ 企业微信 Webhook 未配置")
        return False
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    try:
        response = requests.post(
            WECHAT_WEBHOOK,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        errcode = result.get('errcode', -1)
        
        if errcode == 0:
            print("  ✓ 消息推送成功")
            return True
        elif errcode == 93004:
            print(f"  ✗ 推送失败: 请求过快,请降低频率")
            return False
        elif errcode == 301005:
            print(f"  ✗ 推送失败: 消息长度超限")
            return False
        else:
            print(f"  ✗ 推送失败 (errcode {errcode}): {result.get('errmsg', '未知错误')}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"  ✗ 推送请求超时 (>{REQUEST_TIMEOUT}秒)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 推送请求失败: {str(e)[:100]}")
        return False


def format_articles_message(articles: List[Dict], batch_num: int = 1, total_batches: int = 1, total_count: int = None) -> str:
    """
    格式化文章列表为 Markdown 消息
    
    格式示例:
    📰 AI 资讯精选 (2026-02-26 20:12) - 第4/4批
    本批 7 篇 / 共 43 篇新文章：
    1. [来源] 文章标题(截断至64字符)... [分类]
    
    Args:
        articles: 文章列表
        batch_num: 当前批次号
        total_batches: 总批次数
        total_count: 总文章数
    
    Returns:
        Markdown 格式的消息内容
    """
    shanghai_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M")
    
    if total_count is None:
        total_count = len(articles)
    
    # 构建标题
    if total_batches > 1:
        title = f"📰 AI 资讯精选 ({current_time}) - 第{batch_num}/{total_batches}批\n"
        title += f"本批 {len(articles)} 篇 / 共 {total_count} 篇新文章：\n"
    else:
        title = f"📰 AI 资讯精选 ({current_time})\n"
        title += f"本期 {len(articles)} 篇新文章：\n"
    
    markdown_content = title
    
    # 文章列表 - 简洁格式
    for i, article in enumerate(articles, 1):
        # 基本信息
        full_title = article.get('title', '无标题')
        link = article.get('link', article.get('url', ''))
        source = article.get('source_name', '未知来源')
        
        # 清理标题: 移除换行符,避免破坏 Markdown 链接格式
        full_title = full_title.replace('\n', ' ').replace('\r', ' ')
        # 合并多个空格为一个
        full_title = ' '.join(full_title.split())
        
        # 标题截断至64字符
        if len(full_title) > 64:
            title_text = full_title[:64] + '...'
        else:
            title_text = full_title
        
        # 转义 Markdown 特殊字符,防止破坏链接格式
        # 需要转义: [ ] ( ) 等在链接文本中可能引起歧义的字符
        title_text_escaped = (title_text
            .replace('[', '\\[')
            .replace(']', '\\]')
            .replace('(', '\\(')
            .replace(')', '\\)'))
        
        # 分类标签
        categories = article.get('categories', [])
        category_str = ' | '.join(categories) if categories else ''
        category_tag = f" [{category_str}]" if category_str else ""
        
        # 格式: 序号. [来源] 标题... [分类]
        # 如果有链接,标题添加超链接
        if link:
            markdown_content += f"{i}. [{source}] [{title_text_escaped}]({link}){category_tag}\n"
        else:
            markdown_content += f"{i}. [{source}] {title_text}{category_tag}\n"
    
    markdown_content += "*Powered by n8n + AI 筛选*"
    
    return markdown_content


def push_articles(articles: List[Dict]) -> bool:
    """
    推送文章列表到企业微信(支持自动分批)
    
    Args:
        articles: 文章列表
    
    Returns:
        是否全部推送成功
    """
    if not articles:
        print("  ℹ️ 没有文章需要推送")
        return True
    
    total_count = len(articles)
    print(f"\n📤 步骤 5: 推送到企业微信")
    print(f"  📋 待推送: {total_count} 篇文章")
    
    # 智能分批策略
    batches = []
    current_batch = []
    
    for article in articles:
        current_batch.append(article)
        
        # 策略1: 数量超过限制,强制分批
        if len(current_batch) >= MAX_ARTICLES_PER_BATCH:
            batches.append(current_batch)
            current_batch = []
            continue
        
        # 策略2: 检查消息字节长度
        test_message = format_articles_message(current_batch, 1, 1)
        test_bytes = len(test_message.encode('utf-8'))
        
        if test_bytes > MAX_MESSAGE_BYTES:
            # 超出限制，移除最后一篇，保存当前批次
            if len(current_batch) > 1:
                current_batch.pop()
                batches.append(current_batch)
                # 开始新批次，包含被移除的文章
                current_batch = [article]
            else:
                # 单篇文章就超长，简化格式
                print(f"  ⚠️ 单篇文章过长，将简化内容: {article.get('title', '')[:50]}")
                # 简化：移除推荐理由
                article['reason'] = article.get('reason', '')[:20] + '...'
                batches.append([article])
                current_batch = []
    
    # 添加最后一批
    if current_batch:
        batches.append(current_batch)
    
    total_batches = len(batches)
    
    if total_batches > 1:
        print(f"  ℹ️ 将分 {total_batches} 批推送 (每批最多 {MAX_ARTICLES_PER_BATCH} 篇)")
    
    # 逐批推送
    all_success = True
    for batch_num, batch_articles in enumerate(batches, 1):
        print(f"\n  📦 正在推送第 {batch_num}/{total_batches} 批 ({len(batch_articles)} 篇文章)")
        
        # 格式化消息
        message = format_articles_message(batch_articles, batch_num, total_batches, total_count)
        message_bytes = len(message.encode('utf-8'))
        print(f"     消息大小: {message_bytes} 字节")
        
        # 最后检查：企业微信按字节计算
        if message_bytes > 4096:
            print(f"  ⚠️ 消息超长，强制截断")
            message_encoded = message.encode('utf-8')[:4000]
            try:
                message = message_encoded.decode('utf-8')
            except UnicodeDecodeError:
                # 截断位置在多字节字符中间，向前找安全位置
                for i in range(4000, 3990, -1):
                    try:
                        message = message.encode('utf-8')[:i].decode('utf-8')
                        break
                    except:
                        continue
            message += "\n\n...(内容过长,已截断)"
        
        # 发送
        success = send_markdown(message)
        
        if not success:
            all_success = False
            print(f"  ✗ 第 {batch_num} 批推送失败")
        
        # 批次间暂停,避免频繁请求
        if batch_num < total_batches:
            print(f"  ⏳ 等待 {BATCH_INTERVAL} 秒后发送下一批...")
            time.sleep(BATCH_INTERVAL)
    
    if all_success:
        print(f"\n  ✓ 推送成功: {total_count} 篇文章")
    else:
        print(f"\n  ⚠️ 推送部分失败")
    
    return all_success


def send_test_message() -> bool:
    """发送测试消息"""
    shanghai_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    test_content = f"""## 🧪 测试消息

🤖 RSS AI 推送系统测试

如果您看到这条消息，说明推送配置正确！

---
*发送时间: {current_time}*"""
    
    return send_markdown(test_content)


def main():
    """测试函数"""
    print("=" * 60)
    print("🧪 企业微信推送模块测试")
    print("=" * 60)
    
    # 测试消息
    print("\n📤 测试 1: 发送测试消息")
    if send_test_message():
        print("✅ 测试消息发送成功")
    else:
        print("❌ 测试消息发送失败")
        return
    
    # 等待
    print("\n⏳ 等待 3 秒后继续...")
    time.sleep(3)
    
    # 测试文章推送
    test_articles = [
        {
            "title": "《2028年全球智力危机》：当人类智力不再稀缺，黄昏真的会到来？ |【经纬低调分享】",
            "source_name": "经纬创投",
            "link": "https://example.com/1",
            "categories": ["AI产品"],
        },
        {
            "title": "当 MiniMax 遇见 OpenClaw：「1 2 3 上链接」",
            "source_name": "十字路口Crossing",
            "link": "https://example.com/2",
            "categories": ["AI初创"],
        },
        {
            "title": "深度｜Claude Code创造者：面向六个月后模型开发，而非当下模型；未来人人皆可开发软件，跨领域通才更具竞争力",
            "source_name": "Z Potentials",
            "link": "https://example.com/3",
            "categories": ["大模型", "AI产品"],
        },
        {
            "title": "速递｜企业需要\"被AI找到\"：SIG和光速创投领投，AI搜索营销平台Gushwork完成900万美元种子轮融资",
            "source_name": "Z Potentials",
            "link": "https://example.com/4",
            "categories": ["AI融资", "AI初创"],
        }
    ]
    
    print("\n📤 测试 2: 推送测试文章")
    if push_articles(test_articles):
        print("\n✅ 文章推送测试成功")
    else:
        print("\n❌ 文章推送测试失败")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！请检查企业微信群消息")
    print("=" * 60)


if __name__ == "__main__":
    main()
