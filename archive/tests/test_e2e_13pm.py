#!/usr/bin/env python3
"""
端到端测试: 模拟13点推送流程
使用API4接口获取文章 → AI筛选 → 格式化消息 → 模拟推送
"""

import sys
import json
import requests
import time
from datetime import datetime

# 添加src到路径
sys.path.insert(0, '/root/project-wb/n8n/src')

# API4配置
API4_BASE_URL = "http://www.jintiankansha.me/api3/query"
API4_USER = "your-email@example.com"
API4_TOKEN = "YOUR_API4_TOKEN"

# AI筛选配置
AI_API_URL = "http://your-llm-api-host/agent"
AI_API_KEY = "YOUR_LLM_API_KEY"
AI_MODEL = "kimi-k2.5-ioa"

# 测试参数
TEST_BATCH_SIZE = 15  # 每批处理15篇
MAX_ARTICLES_PER_SOURCE = 20  # 每个源最多20篇

def fetch_articles_from_source(slug, source_name):
    """从单个公众号获取文章"""
    try:
        url = f"{API4_BASE_URL}/get_topics_by_one_column"
        params = {
            "user": API4_USER,
            "token": API4_TOKEN,
            "slug": slug
        }
        
        print(f"  📡 正在获取 {source_name} 的文章...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 503:
            print(f"  ⚠️ {source_name}: 限流(503)")
            return []
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            api_articles = data.get("data", [])
            articles = []
            
            for item in api_articles[:MAX_ARTICLES_PER_SOURCE]:
                articles.append({
                    'title': item.get('name', '').strip(),
                    'link': item.get('original_url', '').strip(),
                    'summary': '',
                    'source_name': source_name,
                    'publish_time': item.get('publish_time', ''),
                    'image': item.get('image', '')
                })
            
            print(f"  ✓ {source_name}: {len(articles)} 篇")
            return articles
        else:
            print(f"  ✗ {source_name}: API错误")
            return []
            
    except Exception as e:
        print(f"  ✗ {source_name}: {str(e)[:50]}")
        return []

def call_ai_filter(articles):
    """调用AI进行筛选 - 使用llm_filter.py中的正确格式"""
    # 构建提示词 - 与llm_filter.py保持一致
    articles_text = "\n\n".join([
        f"{i + 1}. 标题: {a.get('title', '')}\n   摘要: {a.get('summary', '')[:200] or '(无摘要)'}\n   来源: {a.get('source_name', '')}"
        for i, a in enumerate(articles)
    ])
    
    prompt = f"""请判断以下文章是否与"AI、人工智能、大模型、AIGC、创业、融资"相关。

文章列表:
{articles_text}

判断标准:
1. 直接讨论 AI、人工智能、机器学习、大模型、AIGC 等技术
2. 涉及 AI 创业公司、商业模式创新
3. 报道 AI 领域的融资、投资、估值等商业资讯
4. AI 科技公司的重要动态(IPO、并购、新产品发布等)
5. AI 应用、AI 工具、AI Agent 等产品

请对每篇文章判断其相关性,并为相关文章分配 1-3 个分类标签:
- AIGC: 生成式 AI、内容生成、文生图、文生视频
- AI初创: AI 公司、AI 创业、AI 企业
- AI融资: AI 投资、AI 估值、AI IPO
- 大模型: LLM、GPT、Claude、Transformer
- AI产品: AI 应用、AI 工具、AI 助手、AI Agent

**重要**: 请只输出 JSON 格式，不要包含文章标题的完整文本(避免特殊字符导致格式错误)。

请输出严格的 JSON 格式:
{{
  "results": [
    {{
      "index": 1,
      "relevant": true,
      "categories": ["大模型", "AI产品"],
      "reason": "简要说明匹配原因(不超过30字)"
    }},
    {{
      "index": 2,
      "relevant": false,
      "categories": [],
      "reason": "与 AI 主题无关"
    }}
  ]
}}

注意:
1. 请移除 title 字段，避免特殊字符导致 JSON 格式错误
2. reason 字段请保持简短(不超过30字)
3. 确保 JSON 格式正确，可以被标准解析器解析
4. 对每篇文章都给出判断，不要遗漏"""
    
    # 调用AI API - 使用正确的格式
    payload = {
        "prompt": prompt,
        "print": True,
        "dangerouslySkipPermissions": True
    }
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print(f"\n  🤖 调用AI筛选 ({len(articles)}篇文章)...")
    
    try:
        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=60)
        
        print(f"  📊 响应状态码: {response.status_code}")
        
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # API返回纯文本，不是JSON
        content = response.text.strip()
        
        if not content:
            print(f"  ✗ AI返回空响应")
            return [], ""
        
        print(f"  ✓ AI返回成功 (长度: {len(content)}字符)")
        print(f"  📄 响应前200字符: {content[:200]}")
        
        # 提取JSON
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content, re.MULTILINE | re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1).strip()
            print(f"  ✓ 找到JSON代码块")
        else:
            # 查找{ ... }
            start_pos = content.find('{')
            if start_pos == -1:
                print(f"  ✗ 未找到JSON")
                return [], content
            
            brace_count = 0
            end_pos = -1
            for i in range(start_pos, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos == -1:
                print(f"  ✗ JSON括号不匹配")
                return [], content
            
            json_str = content[start_pos:end_pos].strip()
            print(f"  ✓ 提取JSON对象")
        
        result = json.loads(json_str)
        
        # 解析结果 - 使用llm_filter.py中的格式
        results_list = result.get("results", [])
        
        filtered = []
        for item in results_list:
            if not item.get("relevant", False):
                continue
            
            index = item.get("index", 0) - 1  # 转为0-based
            if 0 <= index < len(articles):
                article = articles[index].copy()
                article['categories'] = item.get("categories", [])
                article['reason'] = item.get("reason", "")
                filtered.append(article)
        
        print(f"  ✓ AI筛选完成: {len(filtered)}/{len(articles)} 篇相关")
        return filtered, content
        
    except Exception as e:
        print(f"  ✗ AI调用失败: {e}")
        import traceback
        traceback.print_exc()
        return [], ""

def format_message(articles):
    """格式化推送消息"""
    if not articles:
        return ""
    
    lines = [
        "📰 **AI资讯精选**",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"本次推送 {len(articles)} 篇优质AI内容：",
        ""
    ]
    
    for i, article in enumerate(articles, 1):
        categories = article.get('categories', [])
        cat_str = ' | '.join(categories) if categories else '其他'
        
        lines.append(f"**{i}. {article['title']}**")
        lines.append(f"📂 {cat_str}")
        lines.append(f"📰 来源: {article['source_name']}")
        
        if article.get('reason'):
            lines.append(f"💡 {article['reason']}")
        
        if article.get('link'):
            lines.append(f"🔗 [查看原文]({article['link']})")
        
        lines.append("")
    
    lines.append("---")
    lines.append("_由AI智能筛选_")
    
    return "\n".join(lines)

def main():
    """主测试流程"""
    print("=" * 70)
    print("🧪 端到端测试: 模拟13点推送流程")
    print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   批次大小: {TEST_BATCH_SIZE}篇")
    print("=" * 70)
    
    # 步骤1: 读取RSS源配置
    print("\n📋 步骤1: 读取RSS源配置")
    try:
        with open('/root/project-wb/n8n/config/rss-sources.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        sources = [s for s in config.get('sources', []) if s.get('enabled', False)]
        print(f"  ✓ 找到 {len(sources)} 个启用的源")
        
        # 只测试前3个源
        test_sources = sources[:3]
        print(f"  📌 本次测试: {len(test_sources)} 个源")
        for s in test_sources:
            print(f"     - {s['name']}")
        
    except Exception as e:
        print(f"  ✗ 读取配置失败: {e}")
        return 1
    
    # 步骤2: 获取文章
    print("\n📥 步骤2: 获取文章 (API4接口)")
    all_articles = []
    
    for source in test_sources:
        articles = fetch_articles_from_source(source.get('slug', ''), source['name'])
        all_articles.extend(articles)
        time.sleep(1)  # 避免限流
    
    print(f"\n  📊 总计: {len(all_articles)} 篇文章")
    
    if not all_articles:
        print("  ✗ 没有获取到文章")
        return 1
    
    # 取前15篇作为测试批次
    test_batch = all_articles[:TEST_BATCH_SIZE]
    print(f"  📦 测试批次: {len(test_batch)} 篇")
    
    # 步骤3: AI筛选
    print("\n🤖 步骤3: AI智能筛选")
    filtered_articles, ai_response = call_ai_filter(test_batch)
    
    if not filtered_articles:
        print("  ℹ️ 没有文章通过筛选")
        print(f"\n  🔍 AI原始响应:\n{ai_response[:500]}")
        return 0
    
    # 显示筛选结果
    print(f"\n  ✅ 筛选结果: {len(filtered_articles)}/{len(test_batch)} 篇")
    print("\n  📊 筛选详情:")
    for i, article in enumerate(filtered_articles, 1):
        cats = ' | '.join(article.get('categories', []))
        print(f"    {i}. [{cats}] {article['title'][:50]}...")
        print(f"       💡 {article.get('reason', 'N/A')}")
    
    # 步骤4: 格式化消息
    print("\n📝 步骤4: 格式化推送消息")
    message = format_message(filtered_articles)
    
    print("\n" + "=" * 70)
    print("📤 最终推送消息预览:")
    print("=" * 70)
    print(message)
    print("=" * 70)
    
    # 步骤5: 模拟推送(不实际发送)
    print("\n📮 步骤5: 模拟推送")
    print("  ℹ️ 测试模式 - 不实际发送到企业微信")
    print(f"  ✓ 消息长度: {len(message)} 字符")
    print(f"  ✓ 包含文章: {len(filtered_articles)} 篇")
    
    # 总结
    print("\n" + "=" * 70)
    print("✅ 端到端测试完成")
    print(f"   获取文章: {len(all_articles)} 篇")
    print(f"   测试批次: {len(test_batch)} 篇")
    print(f"   AI筛选: {len(filtered_articles)} 篇 ({len(filtered_articles)/len(test_batch)*100:.1f}%)")
    print(f"   消息格式: ✓")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
