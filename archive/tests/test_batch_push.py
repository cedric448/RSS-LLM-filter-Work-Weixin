#!/usr/bin/env python3
"""
测试分批推送功能 - 模拟超过20篇文章的推送
"""
import sys
sys.path.insert(0, '/root/project-wb/n8n/src')

from wechat_pusher import push_articles

def test_batch_push():
    """测试分批推送(模拟25篇文章)"""
    
    # 生成25篇测试文章
    test_articles = []
    for i in range(1, 26):
        test_articles.append({
            "title": f"AI资讯{i}: 大模型技术突破与应用创新",
            "summary": f"这是第{i}篇文章的摘要内容...",
            "source_name": f"AI媒体{(i-1)%5+1}",
            "link": f"https://example.com/article{i}",
            "categories": ["大模型", "AI产品"] if i % 2 == 0 else ["AI融资", "AI初创"],
            "reason": f"测试文章{i}"
        })
    
    print("=" * 60)
    print(f"🧪 测试分批推送功能 - 共 {len(test_articles)} 篇文章")
    print("=" * 60)
    
    # 执行推送
    success = push_articles(test_articles)
    
    if success:
        print("\n✅ 分批推送测试成功!")
        print(f"   预期: 分2批推送 (第1批20篇, 第2批5篇)")
    else:
        print("\n❌ 分批推送测试失败!")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    test_batch_push()
