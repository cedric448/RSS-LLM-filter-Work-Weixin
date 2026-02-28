#!/usr/bin/env python3
"""
RSS 智能筛选自动推送脚本
定时执行: 每天 9:00, 13:00, 20:00
增加去重机制: 避免重复推送已推送的文章
"""

import sys
import os
import json
import requests
import hashlib
import sqlite3
import time
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加src到路径
sys.path.insert(0, '/root/project-wb/n8n/src')

from llm_filter import filter_articles_batch
from wechat_pusher import push_articles

# 配置
RSS_SOURCES_CONFIG = "/root/project-wb/n8n/config/rss-sources.json"
PUSH_HISTORY_DB = "/root/project-wb/n8n/data/push_history.db"
MAX_ARTICLES_PER_SOURCE = 20  # 每个源最多获取20篇
HISTORY_RETENTION_DAYS = 30  # 保留30天的推送历史
RSS_FETCH_TIMEOUT = 15  # RSS获取超时时间(秒)
MAX_CONCURRENT_RSS = 3  # 最大并发RSS获取数 (参考文档建议3)
RSS_MAX_RETRIES = 3  # RSS获取失败重试次数 (参考文档建议3)
RSS_RETRY_DELAY = 3  # 重试间隔(秒,指数退避)
REQUEST_INTERVAL = 1.0  # 请求间隔(秒) 避免限流

# API4配置
USE_API4 = True  # 使用API接口四(True)或RSS方式(False)
API4_BASE_URL = "http://www.jintiankansha.me/api3/query"
API4_USER = os.environ.get('API4_USER', 'your-email@example.com')
API4_TOKEN = os.environ.get('API4_TOKEN', 'your-api-token-here')

# 初始化数据库
def init_database():
    """初始化推送历史数据库"""
    # 确保数据目录存在
    db_dir = Path(PUSH_HISTORY_DB).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(PUSH_HISTORY_DB)
    cursor = conn.cursor()
    
    # 创建推送历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_hash TEXT UNIQUE NOT NULL,
            title TEXT,
            link TEXT,
            source_name TEXT,
            push_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_article_hash ON push_history(article_hash)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_push_time ON push_history(push_time)
    ''')
    
    conn.commit()
    conn.close()

def get_article_hash(article):
    """生成文章唯一哈希（基于链接或标题）"""
    # 优先使用链接，如果没有链接则使用标题+来源
    unique_str = article.get('link', '') or f"{article.get('title', '')}_{article.get('source_name', '')}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

def is_article_pushed(article):
    """检查文章是否已推送"""
    article_hash = get_article_hash(article)
    
    conn = sqlite3.connect(PUSH_HISTORY_DB)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT COUNT(*) FROM push_history WHERE article_hash = ?',
        (article_hash,)
    )
    count = cursor.fetchone()[0]
    
    conn.close()
    return count > 0

def mark_articles_as_pushed(articles):
    """标记文章为已推送"""
    if not articles:
        return
    
    conn = sqlite3.connect(PUSH_HISTORY_DB)
    cursor = conn.cursor()
    
    # 使用本地时间 (Asia/Shanghai)
    local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for article in articles:
        article_hash = get_article_hash(article)
        
        try:
            cursor.execute('''
                INSERT INTO push_history (article_hash, title, link, source_name, push_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                article_hash,
                article.get('title', '')[:200],  # 限制长度
                article.get('link', ''),
                article.get('source_name', ''),
                local_time
            ))
        except sqlite3.IntegrityError:
            # 如果已存在（唯一约束冲突），跳过
            pass
    
    conn.commit()
    conn.close()

def clean_old_history():
    """清理旧的推送历史（保留最近N天）"""
    conn = sqlite3.connect(PUSH_HISTORY_DB)
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
    
    cursor.execute(
        'DELETE FROM push_history WHERE push_time < ?',
        (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),)
    )
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        print(f"  🗑️ 清理了 {deleted_count} 条超过 {HISTORY_RETENTION_DAYS} 天的历史记录")
    
    return deleted_count

def get_push_statistics():
    """获取推送统计信息"""
    conn = sqlite3.connect(PUSH_HISTORY_DB)
    cursor = conn.cursor()
    
    # 总推送数
    cursor.execute('SELECT COUNT(*) FROM push_history')
    total_count = cursor.fetchone()[0]
    
    # 今天推送数
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'SELECT COUNT(*) FROM push_history WHERE DATE(push_time) = ?',
        (today,)
    )
    today_count = cursor.fetchone()[0]
    
    # 最近一次推送时间
    cursor.execute(
        'SELECT MAX(push_time) FROM push_history'
    )
    last_push = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_count,
        'today': today_count,
        'last_push': last_push
    }

def get_rss_sources():
    """从配置文件读取 RSS 源列表"""
    try:
        with open(RSS_SOURCES_CONFIG, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sources = data.get('sources', [])
        # 只返回启用的源
        enabled_sources = [s for s in sources if s.get('enabled', False)]
        print(f"✓ 读取到 {len(enabled_sources)} 个启用的 RSS 源")
        return enabled_sources
    except Exception as e:
        print(f"✗ 读取 RSS 源配置失败: {e}")
        return []

def fetch_rss_articles(url, source_name, retry_count=0):
    """获取单个 RSS 源的文章(支持重试)"""
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        
        # 检查503错误 - 服务端限流，等待后重试
        if response.status_code == 503:
            if retry_count < RSS_MAX_RETRIES:
                delay = 5  # 503错误固定等待5秒
                print(f"  ⏳ {source_name}: 限流(503)，{delay}秒后重试 ({retry_count + 1}/{RSS_MAX_RETRIES})")
                time.sleep(delay)
                return fetch_rss_articles(url, source_name, retry_count + 1)
            else:
                print(f"  ✗ {source_name}: 限流(503)，重试{RSS_MAX_RETRIES}次后仍失败")
                return []
        
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles = []
        
        for item in root.findall('.//item')[:MAX_ARTICLES_PER_SOURCE]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            
            if title_elem is not None and title_elem.text:
                articles.append({
                    'title': title_elem.text.strip(),
                    'link': link_elem.text.strip() if link_elem is not None and link_elem.text else '',
                    'summary': (desc_elem.text or '')[:500] if desc_elem is not None else '',
                    'source_name': source_name
                })
        
        # 成功获取
        retry_suffix = f" (重试{retry_count}次后成功)" if retry_count > 0 else ""
        print(f"  ✓ {source_name}: {len(articles)} 篇文章{retry_suffix}")
        return articles
        
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # 可重试的错误
        if retry_count < RSS_MAX_RETRIES:
            # 指数退避: 3秒, 6秒
            delay = RSS_RETRY_DELAY * (2 ** retry_count)
            print(f"  ⏳ {source_name}: {'超时' if isinstance(e, requests.exceptions.Timeout) else '连接失败'}, {delay}秒后重试 ({retry_count + 1}/{RSS_MAX_RETRIES})")
            time.sleep(delay)
            return fetch_rss_articles(url, source_name, retry_count + 1)
        else:
            print(f"  ✗ {source_name}: 重试{RSS_MAX_RETRIES}次后仍失败")
            return []
    except Exception as e:
        # 其他错误不重试
        print(f"  ✗ {source_name}: 获取失败 - {str(e)[:100]}")
        return []

def fetch_articles_via_api4(slug, source_name, retry_count=0):
    """通过API接口四获取文章(支持重试)"""
    try:
        url = f"{API4_BASE_URL}/get_topics_by_one_column"
        params = {
            "user": API4_USER,
            "token": API4_TOKEN,
            "slug": slug
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # 检查503错误 - 服务端限流，等待后重试
        if response.status_code == 503:
            if retry_count < RSS_MAX_RETRIES:
                delay = 5  # 503错误固定等待5秒
                print(f"  ⏳ {source_name}: 限流(503)，{delay}秒后重试 ({retry_count + 1}/{RSS_MAX_RETRIES})")
                time.sleep(delay)
                return fetch_articles_via_api4(slug, source_name, retry_count + 1)
            else:
                print(f"  ✗ {source_name}: 限流(503)，重试{RSS_MAX_RETRIES}次后仍失败")
                return []
        
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "success":
            api_articles = data.get("data", [])
            articles = []
            
            # 转换API4格式到标准格式
            for item in api_articles[:MAX_ARTICLES_PER_SOURCE]:
                articles.append({
                    'title': item.get('name', '').strip(),
                    'link': item.get('original_url', '').strip(),
                    'summary': '',  # API4不返回摘要，留空
                    'source_name': source_name,
                    'publish_time': item.get('publish_time', ''),  # 格式: YYYYMMDDHHMMSS
                    'image': item.get('image', '')  # API4额外字段
                })
            
            retry_suffix = f" (重试{retry_count}次后成功)" if retry_count > 0 else ""
            print(f"  ✓ {source_name}: {len(articles)} 篇文章{retry_suffix}")
            return articles
        else:
            error_msg = data.get('data', {}).get('message', 'Unknown error')
            print(f"  ✗ {source_name}: API返回错误 - {error_msg}")
            return []
            
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # 可重试的错误
        if retry_count < RSS_MAX_RETRIES:
            delay = RSS_RETRY_DELAY * (2 ** retry_count)
            print(f"  ⏳ {source_name}: {'超时' if isinstance(e, requests.exceptions.Timeout) else '连接失败'}, {delay}秒后重试 ({retry_count + 1}/{RSS_MAX_RETRIES})")
            time.sleep(delay)
            return fetch_articles_via_api4(slug, source_name, retry_count + 1)
        else:
            print(f"  ✗ {source_name}: 重试{RSS_MAX_RETRIES}次后仍失败")
            return []
    except Exception as e:
        print(f"  ✗ {source_name}: 获取失败 - {str(e)[:100]}")
        return []

def fetch_rss_articles_concurrent(sources):
    """并发获取多个RSS源的文章"""
    all_articles = []
    success_count = 0
    fail_count = 0
    
    # 源较多时降低并发数,避免限流
    actual_concurrent = min(MAX_CONCURRENT_RSS, 3) if len(sources) > 10 else MAX_CONCURRENT_RSS
    if actual_concurrent < MAX_CONCURRENT_RSS:
        print(f"  ℹ️ 源较多({len(sources)}个),自动降低并发数至 {actual_concurrent}")
    
    with ThreadPoolExecutor(max_workers=actual_concurrent) as executor:
        # 提交所有任务 - 根据USE_API4选择方法
        if USE_API4:
            future_to_source = {
                executor.submit(
                    fetch_articles_via_api4, 
                    source.get('slug', ''), 
                    source['name']
                ): source 
                for source in sources
                if source.get('slug')  # 只处理有slug的源
            }
        else:
            future_to_source = {
                executor.submit(fetch_rss_articles, source['url'], source['name']): source 
                for source in sources
            }
        
        # 等待完成
        for i, future in enumerate(as_completed(future_to_source)):
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
                    success_count += 1
                else:
                    fail_count += 1
                
                # 请求间隔,避免限流
                if i < len(future_to_source) - 1:
                    time.sleep(REQUEST_INTERVAL)
            except Exception as e:
                source = future_to_source[future]
                print(f"  ✗ {source['name']}: 异常 - {e}")
                fail_count += 1
    
    return all_articles, success_count, fail_count

def filter_new_articles(articles):
    """过滤出未推送的新文章"""
    new_articles = []
    duplicate_count = 0
    
    for article in articles:
        if not is_article_pushed(article):
            new_articles.append(article)
        else:
            duplicate_count += 1
    
    if duplicate_count > 0:
        print(f"  ℹ️ 过滤掉 {duplicate_count} 篇已推送的文章")
    
    return new_articles

def main():
    """主函数"""
    start_time = datetime.now()
    print("=" * 60)
    print(f"🚀 RSS 智能筛选自动推送")
    print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   获取方式: {'API接口四 (JSON)' if USE_API4 else 'RSS方式 (XML)'}")
    print("=" * 60)
    
    # 初始化数据库
    init_database()
    
    # 显示推送统计
    stats = get_push_statistics()
    print(f"\n📊 推送统计:")
    print(f"   历史总推送: {stats['total']} 篇")
    print(f"   今日已推送: {stats['today']} 篇")
    if stats['last_push']:
        print(f"   最近推送: {stats['last_push']}")
    
    # 清理旧历史
    clean_old_history()
    
    # 1. 获取 RSS 源列表
    print("\n📥 步骤 1: 获取 RSS 源列表")
    sources = get_rss_sources()
    
    if not sources:
        print("✗ 没有可用的 RSS 源，退出")
        return 1
    
    # 2. 并发获取所有文章
    print(f"\n📰 步骤 2: 并发获取文章")
    print(f"  ⚙️ 每源最多: {MAX_ARTICLES_PER_SOURCE} 篇")
    print(f"  ⚙️ 最大并发: {MAX_CONCURRENT_RSS}")
    print(f"  ⚙️ 请求间隔: {REQUEST_INTERVAL}秒")
    all_articles, success_count, fail_count = fetch_rss_articles_concurrent(sources)
    
    print(f"\n  总计: {len(all_articles)} 篇文章")
    print(f"  成功: {success_count} 个源")
    if fail_count > 0:
        print(f"  失败: {fail_count} 个源")
    
    if not all_articles:
        print("✗ 没有获取到任何文章，退出")
        return 1
    
    # 3. 过滤已推送的文章（去重）
    print(f"\n🔍 步骤 3: 过滤重复文章")
    new_articles = filter_new_articles(all_articles)
    
    print(f"  ✓ 新文章: {len(new_articles)}/{len(all_articles)} 篇")
    
    if not new_articles:
        print("\n  ℹ️ 没有新文章，无需推送")
        return 0
    
    # 4. AI 筛选
    # (LLM模块内部已有详细日志,这里简化)
    try:
        filtered_articles = filter_articles_batch(new_articles)
        
        if filtered_articles:
            print(f"\n  📊 筛选文章预览:")
            for i, article in enumerate(filtered_articles[:5], 1):
                categories = article.get('categories', [])
                cat_str = ' | '.join(categories) if categories else '无'
                confidence = article.get('confidence', 0)
                title_preview = article['title'][:40] + ('...' if len(article['title']) > 40 else '')
                print(f"    {i}. [{article['source_name']}] {title_preview} [{cat_str}] (置信度: {confidence:.2f})")
            if len(filtered_articles) > 5:
                print(f"    ... 还有 {len(filtered_articles) - 5} 篇")
    except Exception as e:
        print(f"  ✗ AI 筛选失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if not filtered_articles:
        print("\n  ℹ️ 没有文章通过筛选，无需推送")
        return 0
    
    # 5. 推送到企业微信
    # (推送模块内部已有详细日志,这里简化)
    try:
        success = push_articles(filtered_articles)
        
        if success:
            # 标记为已推送
            mark_articles_as_pushed(filtered_articles)
            print(f"  ✓ 已标记为已推送")
        else:
            print(f"  ✗ 推送失败")
            return 1
            
    except Exception as e:
        print(f"  ✗ 推送异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 完成
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✅ 推送完成")
    print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   耗时: {duration:.1f} 秒")
    print(f"   获取: {len(all_articles)} 篇")
    print(f"   新文章: {len(new_articles)} 篇 ({len(new_articles)/len(all_articles)*100:.1f}%)")
    print(f"   筛选: {len(filtered_articles)} 篇 ({len(filtered_articles)/len(new_articles)*100:.1f}%)")
    print(f"   推送: {len(filtered_articles)} 篇")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
