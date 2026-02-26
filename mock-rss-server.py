#!/usr/bin/env python3
"""
Mock RSS Server - 模拟今天看啥 RSS API
支持存储 RSS 源配置，提供 RSS 数据接口
"""

from flask import Flask, jsonify, request, Response
import json
import random
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

app = Flask(__name__)

# 存储 RSS 源配置
RSS_SOURCES_FILE = '/root/project-wb/n8n/config/rss-sources.json'

# 模拟文章数据
MOCK_ARTICLES = [
    {
        "title": "OpenAI 发布 GPT-5，性能提升 10 倍",
        "summary": "OpenAI 今日正式发布 GPT-5 大模型，在多项 benchmark 上刷新记录...",
        "category": "大模型",
        "pub_date": "2026-02-20"
    },
    {
        "title": "某 AI 初创公司完成 10 亿美元融资",
        "summary": "专注于企业级 AI 解决方案的初创公司今日宣布完成 B 轮融资...",
        "category": "AI融资",
        "pub_date": "2026-02-20"
    },
    {
        "title": "Midjourney V7 发布，图像生成质量大幅提升",
        "summary": "Midjourney 发布最新版本 V7，支持更精细的图像控制和生成...",
        "category": "AIGC",
        "pub_date": "2026-02-20"
    },
    {
        "title": "字节跳动推出新 AI 产品，对标 ChatGPT",
        "summary": "字节跳动今日发布自研大模型产品，具备多模态理解能力...",
        "category": "AI产品",
        "pub_date": "2026-02-20"
    },
    {
        "title": "2026年 AI 投资趋势报告发布",
        "summary": "报告显示今年 AI 领域投资总额已突破 1000 亿美元...",
        "category": "AI融资",
        "pub_date": "2026-02-20"
    },
    {
        "title": "Claude 4 即将发布，Anthropic 透露新特性",
        "summary": "Anthropic CEO 在接受采访时透露 Claude 4 将具备更强的推理能力...",
        "category": "大模型",
        "pub_date": "2026-02-20"
    },
    {
        "title": "AI 创业公司生存指南：从 0 到 1 的实战经验",
        "summary": "本文分享了 AI 创业过程中的关键决策和踩过的坑...",
        "category": "AI初创",
        "pub_date": "2026-02-20"
    },
    {
        "title": "Stable Diffusion 3 开源，社区反响热烈",
        "summary": "Stability AI 开源了 Stable Diffusion 3 模型，性能超越前代...",
        "category": "AIGC",
        "pub_date": "2026-02-20"
    },
    {
        "title": "某知名 VC 成立 5 亿美元 AI 专项基金",
        "summary": "该基金将专注于投资早期 AI 初创公司，重点关注大模型应用...",
        "category": "AI融资",
        "pub_date": "2026-02-20"
    },
    {
        "title": "Google 发布 Gemini 2.0，多模态能力再升级",
        "summary": "Gemini 2.0 在视频理解、音频生成等方面实现重大突破...",
        "category": "大模型",
        "pub_date": "2026-02-20"
    }
]

def load_rss_sources():
    """加载 RSS 源配置"""
    try:
        with open(RSS_SOURCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"sources": []}

def save_rss_sources(data):
    """保存 RSS 源配置"""
    with open(RSS_SOURCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_rss_xml(source_id, articles):
    """生成 RSS XML 格式数据"""
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = f'公众号 {source_id}'
    ET.SubElement(channel, 'link').text = f'http://example.com/{source_id}'
    ET.SubElement(channel, 'description').text = f'公众号 {source_id} 的 RSS 订阅'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    for article in articles:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = article['title']
        ET.SubElement(item, 'description').text = article['summary']
        ET.SubElement(item, 'link').text = f'http://mp.weixin.qq.com/s/{random.randint(10000, 99999)}'
        ET.SubElement(item, 'pubDate').text = article['pub_date']
        ET.SubElement(item, 'category').text = article['category']
    
    return ET.tostring(rss, encoding='unicode')

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """获取所有 RSS 源"""
    data = load_rss_sources()
    return jsonify(data)

@app.route('/api/sources', methods=['POST'])
def add_source():
    """添加 RSS 源"""
    data = load_rss_sources()
    new_source = request.json
    new_source['id'] = f"source_{len(data['sources']) + 1}"
    new_source['created_at'] = datetime.now().isoformat()
    data['sources'].append(new_source)
    save_rss_sources(data)
    return jsonify({"status": "success", "source": new_source})

@app.route('/api/sources/<source_id>', methods=['DELETE'])
def delete_source(source_id):
    """删除 RSS 源"""
    data = load_rss_sources()
    data['sources'] = [s for s in data['sources'] if s['id'] != source_id]
    save_rss_sources(data)
    return jsonify({"status": "success"})

@app.route('/rss/<source_id>', methods=['GET'])
def get_rss_feed(source_id):
    """获取 RSS feed"""
    # 随机返回 3-8 篇文章
    num_articles = random.randint(3, 8)
    articles = random.sample(MOCK_ARTICLES, min(num_articles, len(MOCK_ARTICLES)))
    
    # 更新发布时间
    for article in articles:
        article['pub_date'] = (datetime.now() - timedelta(hours=random.randint(1, 6))).strftime('%Y-%m-%d %H:%M:%S')
    
    rss_xml = generate_rss_xml(source_id, articles)
    return Response(rss_xml, mimetype='application/rss+xml')

@app.route('/api/articles', methods=['GET'])
def get_all_articles():
    """获取所有文章（JSON 格式）"""
    data = load_rss_sources()
    all_articles = []
    
    for source in data.get('sources', []):
        num_articles = random.randint(2, 5)
        articles = random.sample(MOCK_ARTICLES, min(num_articles, len(MOCK_ARTICLES)))
        for article in articles:
            all_articles.append({
                **article,
                "source_id": source['id'],
                "source_name": source.get('name', 'Unknown'),
                "pub_date": (datetime.now() - timedelta(hours=random.randint(1, 6))).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return jsonify({
        "articles": all_articles,
        "total": len(all_articles),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    # 初始化 RSS 源文件
    import os
    os.makedirs(os.path.dirname(RSS_SOURCES_FILE), exist_ok=True)
    
    if not os.path.exists(RSS_SOURCES_FILE):
        # 创建默认配置
        default_sources = {
            "sources": [
                {"id": "source_1", "name": "AI科技评论", "url": "http://localhost:5000/rss/source_1", "created_at": datetime.now().isoformat()},
                {"id": "source_2", "name": "机器之心", "url": "http://localhost:5000/rss/source_2", "created_at": datetime.now().isoformat()},
                {"id": "source_3", "name": "量子位", "url": "http://localhost:5000/rss/source_3", "created_at": datetime.now().isoformat()}
            ]
        }
        save_rss_sources(default_sources)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
