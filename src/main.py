#!/usr/bin/env python3
"""
RSS AI 推送主程序
集成 RSS 获取、LLM 筛选、企业微信推送
"""
import sys
import requests
import re
from typing import List, Dict
from datetime import datetime

# 导入自定义模块
from llm_filter import filter_articles_batch
from wechat_pusher import push_articles

# RSS 源配置
RSS_SOURCES = [
    {
        "name": "创业邦",
        "url": "http://rss.jintiankansha.me/rss/GE2XYOJZGEYDONBRGQ4GKMJWGI4DSNJZGAZWIZBSGI3DAMTEGY2TIOJYMQ3TOMZWMVQTO==="
    },
    {
        "name": "机器之心",
        "url": "http://rss.jintiankansha.me/rss/G42TC7BZGQ2GCNZRMVSGCZBSGY2GCM3BMI2DKNTEG43GCNTBGVSDQZDBGJQTMNZSGA4WGNI="
    }
]


def parse_rss(xml_content: str, source_name: str) -> List[Dict]:
    """
    解析 RSS XML 内容
    
    Args:
        xml_content: RSS XML 字符串
        source_name: 来源名称
    
    Returns:
        文章列表
    """
    articles = []
    
    # 查找所有 <item> 标签
    item_pattern = re.compile(r'<item[^>]*>(.*?)</item>', re.DOTALL)
    items_matches = item_pattern.findall(xml_content)
    
    for item_xml in items_matches:
        # 提取标题
        title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item_xml)
        title = title_match.group(1) if title_match else ''
        
        # 提取链接
        link_match = re.search(r'<link>(.*?)</link>', item_xml)
        link = link_match.group(1) if link_match else ''
        
        # 提取描述
        desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item_xml, re.DOTALL)
        desc = desc_match.group(1) if desc_match else ''
        # 清理 HTML 标签,只保留纯文本
        desc_clean = re.sub(r'<[^>]+>', '', desc)[:500]
        
        # 提取发布时间
        pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item_xml)
        pubdate = pubdate_match.group(1) if pubdate_match else ''
        
        if title:  # 只添加有标题的文章
            articles.append({
                'title': title.strip(),
                'link': link.strip(),
                'summary': desc_clean.strip(),
                'published': pubdate.strip(),
                'source_name': source_name
            })
    
    return articles


def fetch_rss_articles(max_articles_per_source: int = 20) -> List[Dict]:
    """
    从所有 RSS 源获取文章
    
    Args:
        max_articles_per_source: 每个源最多获取的文章数
    
    Returns:
        文章列表
    """
    print("=" * 60)
    print("📡 开始获取 RSS 文章")
    print("=" * 60)
    
    all_articles = []
    
    for source in RSS_SOURCES:
        name = source['name']
        url = source['url']
        
        print(f"\n📥 获取 {name}...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            articles = parse_rss(response.text, name)
            
            # 限制每个源的文章数量
            articles = articles[:max_articles_per_source]
            
            all_articles.extend(articles)
            print(f"  ✓ 获取 {len(articles)} 篇文章")
            
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")
    
    print(f"\n✅ 共获取 {len(all_articles)} 篇文章")
    return all_articles


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 RSS AI 智能推送系统")
    print("=" * 60)
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. 获取 RSS 文章
        articles = fetch_rss_articles(max_articles_per_source=15)
        
        if not articles:
            print("\n⚠️  没有获取到文章,任务结束")
            return 0
        
        # 2. LLM 智能筛选
        relevant_articles = filter_articles_batch(articles)
        
        if not relevant_articles:
            print("\n⚠️  没有符合条件的文章,不进行推送")
            return 0
        
        # 3. 推送到企业微信
        print("\n" + "=" * 60)
        print("📤 开始推送到企业微信")
        print("=" * 60)
        
        success = push_articles(relevant_articles)
        
        # 4. 输出结果
        print("\n" + "=" * 60)
        if success:
            print("✅ 任务完成！")
            print(f"📊 统计: 获取 {len(articles)} 篇 → 筛选 {len(relevant_articles)} 篇 → 推送成功")
        else:
            print("⚠️  任务完成,但部分推送失败")
            print(f"📊 统计: 获取 {len(articles)} 篇 → 筛选 {len(relevant_articles)} 篇 → 推送异常")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        return 130
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
