#!/usr/bin/env python3
"""
LLM 内容筛选模块
使用大模型进行语义理解,判断文章是否与 AI 主题相关
支持批量处理、重试机制、动态配置
"""
import requests
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple

# 配置路径
KEYWORDS_CONFIG = "/root/project-wb/n8n/config/keywords.json"

# API 配置
LLM_API_URL = "http://119.28.50.67/agent"
LLM_API_KEY = "Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4"
API_TIMEOUT = 120
MAX_RETRIES = 3
RETRY_DELAY = 2
BATCH_SIZE = 15  # 每批处理的文章数量


def load_keywords_config() -> Dict:
    """
    加载关键词配置文件
    
    Returns:
        配置字典,包含 categories, match_mode, threshold
    """
    try:
        with open(KEYWORDS_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"⚠️ 无法加载配置文件 {KEYWORDS_CONFIG}: {e}")
        # 返回默认配置
        return {
            "categories": [
                {"name": "AI相关", "keywords": ["AI", "人工智能"], "description": "AI相关主题"}
            ],
            "match_mode": "semantic",
            "threshold": 0.7
        }


def call_llm_with_retry(prompt: str) -> str:
    """
    调用大模型API(带重试机制)
    
    Args:
        prompt: 提示词
    
    Returns:
        API返回的文本结果
    """
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": LLM_API_KEY
    }
    
    payload = {
        "prompt": prompt,
        "print": True,
        "dangerouslySkipPermissions": True
    }
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                LLM_API_URL,
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            result = response.text.strip()
            
            # 检查返回结果是否有效
            if result and len(result) > 0:
                print(f"  ✓ LLM API 调用成功 (响应长度: {len(result)} 字符)")
                return result
            else:
                print(f"  ⚠️ LLM API 返回空结果,尝试重试 ({attempt + 1}/{MAX_RETRIES})")
        
        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"  ⚠️ LLM API 超时,尝试重试 ({attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  ⚠️ LLM API 请求失败,尝试重试 ({attempt + 1}/{MAX_RETRIES}): {str(e)[:100]}")
        
        # 等待后重试
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
    
    # 所有重试都失败
    print(f"  ✗ 调用大模型 API 失败(已重试 {MAX_RETRIES} 次): {last_error}")
    return ""


def build_batch_prompt(articles: List[Dict], config: Dict, start_index: int = 1) -> str:
    """
    构建批量判断的 prompt
    
    Args:
        articles: 文章列表(包含 title, summary, source_name)
        config: 关键词配置
        start_index: 起始序号
    
    Returns:
        构建好的 prompt
    """
    # 构建文章列表
    articles_text = "\n\n".join([
        f"{start_index + i}. 标题: {a.get('title', '')}\n   摘要: {a.get('summary', '')[:200]}\n   来源: {a.get('source_name', '')}"
        for i, a in enumerate(articles)
    ])
    
    # 构建分类描述
    categories = config.get('categories', [])
    categories_desc = "\n".join([
        f"- {cat['name']}: {cat.get('description', '')} (相关概念: {', '.join(cat.get('keywords', [])[:5])})"
        for cat in categories
    ])
    
    # 获取阈值
    threshold = config.get('threshold', 0.7)
    
    prompt = f"""你是一位专业的 AI 领域内容筛选助手。

任务：判断以下文章是否与 AI 相关，并分类。

筛选规则（语义匹配，非关键词精确匹配）：
{categories_desc}

待筛选文章：
{articles_text}

判断标准:
1. 直接讨论 AI、人工智能、机器学习、大模型、AIGC 等技术
2. 涉及 AI 创业公司、商业模式创新
3. 报道 AI 领域的融资、投资、估值等商业资讯
4. AI 科技公司的重要动态(IPO、并购、新产品发布等)
5. AI 应用、AI 工具、AI Agent 等产品

请对每篇文章判断其相关性,并为相关文章分配 1-3 个分类标签和置信度分数。

**重要**: 
1. 必须对所有 {len(articles)} 篇文章都给出判断(index 从 {start_index} 到 {start_index + len(articles) - 1})
2. 只有置信度 >= {threshold} 的文章才标记为 relevant: true
3. reason 字段请保持简短(不超过30字)
4. 确保输出严格的 JSON 格式

请输出 JSON 格式:
{{
  "results": [
    {{
      "index": {start_index},
      "relevant": true,
      "categories": ["大模型", "AI产品"],
      "reason": "简要说明匹配原因(不超过30字)",
      "confidence": 0.85
    }},
    {{
      "index": {start_index + 1},
      "relevant": false,
      "categories": [],
      "reason": "与 AI 主题无关",
      "confidence": 0.2
    }}
  ]
}}"""
    
    return prompt


def parse_batch_result(result: str, articles: List[Dict], config: Dict, start_index: int = 1) -> Tuple[List[Dict], List[Dict]]:
    """
    解析批量判断结果
    
    Args:
        result: LLM 返回的文本
        articles: 原始文章列表
        config: 配置(包含阈值)
        start_index: 该批次的起始索引
    
    Returns:
        (相关文章列表, 未成功解析的文章列表)
    """
    relevant_articles = []
    failed_articles = []
    threshold = config.get('threshold', 0.7)
    
    try:
        # 提取 JSON 内容
        json_text = extract_json(result)
        if not json_text:
            print(f"  ✗ 无法提取 JSON 内容")
            return [], articles
        
        # 解析 JSON
        parsed = json.loads(json_text)
        results = parsed.get('results', [])
        
        if not results:
            print(f"  ⚠️ JSON 中没有 results 字段或为空")
            return [], articles
        
        print(f"  ✓ 解析到 {len(results)} 条判断结果，预期 {len(articles)} 条")
        
        # 构建索引映射
        ai_judgments = {}
        for r in results:
            global_idx = r.get('index', 0)
            relative_idx = global_idx - start_index
            if 0 <= relative_idx < len(articles):
                ai_judgments[relative_idx] = r
        
        # 处理所有文章
        for i, article in enumerate(articles):
            if i in ai_judgments:
                r = ai_judgments[i]
                confidence = r.get('confidence', 0.0)
                is_relevant = r.get('relevant', False)
                
                # 应用置信度阈值
                if is_relevant and confidence >= threshold:
                    article_copy = article.copy()
                    article_copy['categories'] = r.get('categories', [])
                    article_copy['reason'] = r.get('reason', '')
                    article_copy['confidence'] = confidence
                    relevant_articles.append(article_copy)
                    
                    title_preview = article.get('title', '')[:40]
                    categories_str = ', '.join(article_copy['categories'])
                    print(f"  ✓ 相关 (置信度 {confidence:.2f}): {title_preview} [{categories_str}]")
                else:
                    reason = "低于阈值" if is_relevant else "不相关"
                    print(f"  ✗ {reason} (置信度 {confidence:.2f}): {article.get('title', '')[:40]}")
            else:
                print(f"  ⚠️ 未解析: {article.get('title', '')[:40]}")
                failed_articles.append(article)
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON 解析失败: {e}")
        save_debug_file('/tmp/failed_json.txt', json_text if 'json_text' in locals() else result)
        return [], articles
    except Exception as e:
        print(f"  ✗ 结果解析异常: {e}")
        return [], articles
    
    return relevant_articles, failed_articles


def extract_json(text: str) -> str:
    """
    从文本中提取 JSON 内容
    
    Args:
        text: 原始文本
    
    Returns:
        提取的 JSON 字符串
    """
    # 策略1: 提取 ```json ... ``` 代码块
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.MULTILINE | re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()
        return clean_json_text(json_text)
    
    # 策略2: 查找 { ... } 包裹的 JSON
    start_pos = text.find('{')
    if start_pos == -1:
        return ""
    
    # 使用平衡括号匹配
    brace_count = 0
    end_pos = -1
    for i in range(start_pos, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = i + 1
                break
    
    if end_pos == -1:
        return ""
    
    json_text = text[start_pos:end_pos].strip()
    return clean_json_text(json_text)


def clean_json_text(json_text: str) -> str:
    """
    清理 JSON 文本中的常见问题
    
    Args:
        json_text: 原始 JSON 字符串
    
    Returns:
        清理后的 JSON 字符串
    """
    # 移除 BOM
    json_text = json_text.lstrip('\ufeff')
    
    # 修复中文引号
    json_text = json_text.replace('"', '"').replace('"', '"')
    json_text = json_text.replace(''', "'").replace(''', "'")
    
    # 修复尾随逗号
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # 清理多余的逗号
    json_text = re.sub(r',\s*,', ',', json_text)
    json_text = re.sub(r'{\s*,', '{', json_text)
    json_text = re.sub(r'\[\s*,', '[', json_text)
    
    return json_text


def save_debug_file(filepath: str, content: str):
    """保存调试文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ℹ️ 已保存调试文件: {filepath}")
    except:
        pass


def filter_articles_batch(articles: List[Dict]) -> List[Dict]:
    """
    批量筛选文章
    
    Args:
        articles: 文章列表(每篇需包含 title, summary, source_name, link)
    
    Returns:
        筛选后的文章列表(包含 categories, reason, confidence 字段)
    """
    if not articles:
        return []
    
    # 加载配置
    config = load_keywords_config()
    threshold = config.get('threshold', 0.7)
    
    total_count = len(articles)
    print(f"\n🤖 步骤 4: AI 智能筛选")
    print(f"  📋 待筛选: {total_count} 篇文章")
    print(f"  ⚙️ 批次大小: {BATCH_SIZE} 篇/批")
    print(f"  🎯 置信度阈值: {threshold}")
    
    all_relevant = []
    all_failed = []
    
    # 分批处理
    for i in range(0, total_count, BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n  📦 处理第 {batch_num}/{total_batches} 批 ({len(batch)} 篇)...")
        
        # 构建 prompt
        prompt = build_batch_prompt(batch, config, i + 1)
        
        # 调用 LLM
        result = call_llm_with_retry(prompt)
        
        if not result:
            print(f"  ✗ LLM 调用失败,该批文章全部跳过")
            all_failed.extend(batch)
            continue
        
        # 解析结果
        relevant, failed = parse_batch_result(result, batch, config, i + 1)
        all_relevant.extend(relevant)
        all_failed.extend(failed)
        
        # 批次间延迟
        if batch_num < total_batches:
            time.sleep(1)
    
    print(f"\n  ✓ 筛选结果: {len(all_relevant)}/{total_count} 篇文章符合条件 ({len(all_relevant)/total_count*100:.1f}%)")
    
    if all_failed:
        print(f"  ⚠️ {len(all_failed)} 篇文章筛选失败或未解析")
    
    return all_relevant


def main():
    """测试函数"""
    print("=" * 60)
    print("🧪 LLM 筛选模块测试")
    print("=" * 60)
    
    test_articles = [
        {
            "title": "DeepSeek R1 震撼发布,开源大模型新里程碑",
            "summary": "DeepSeek 公司发布全新 R1 模型,性能媲美 GPT-4,完全开源...",
            "source_name": "机器之心",
            "link": "https://example.com/1"
        },
        {
            "title": "今天中午吃什么?10 家餐厅推荐",
            "summary": "精选 10 家美食餐厅,让你不再为午餐发愁...",
            "source_name": "美食日报",
            "link": "https://example.com/2"
        },
        {
            "title": "OpenAI 获 100 亿美元融资,估值达 800 亿",
            "summary": "OpenAI 完成新一轮融资,估值再创新高,将继续投入 AGI 研发...",
            "source_name": "创业邦",
            "link": "https://example.com/3"
        }
    ]
    
    results = filter_articles_batch(test_articles)
    
    print("\n" + "=" * 60)
    print("📋 筛选结果:")
    print("=" * 60)
    for i, article in enumerate(results, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   来源: {article['source_name']}")
        print(f"   分类: {', '.join(article.get('categories', []))}")
        print(f"   置信度: {article.get('confidence', 0):.2f}")
        print(f"   理由: {article.get('reason', '')}")
        print(f"   链接: {article['link']}")


if __name__ == "__main__":
    main()
