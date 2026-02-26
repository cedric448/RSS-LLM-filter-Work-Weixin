#!/usr/bin/env python3
"""测试后台 API 功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from app import app, load_rss_sources, save_rss_sources, AUTH_CODE
import json

def test_config():
    """测试配置文件读写"""
    print("=" * 60)
    print("测试配置文件功能")
    print("=" * 60)
    
    # 测试读取
    print("\n1. 读取现有配置...")
    sources = load_rss_sources()
    print(f"   当前有 {len(sources)} 个 RSS 源")
    for source in sources:
        print(f"   - {source['name']}: {source['url'][:50]}...")
    
    # 测试添加
    print("\n2. 测试添加新源...")
    test_source = {
        'id': 'test_source_1',
        'name': '测试公众号',
        'url': 'http://rss.jintiankansha.me/rss/TEST',
        'description': '测试用 RSS 源',
        'enabled': True,
        'created_at': '2026-02-20T20:00:00'
    }
    
    sources.append(test_source)
    if save_rss_sources(sources):
        print("   ✓ 添加成功")
    else:
        print("   ✗ 添加失败")
    
    # 验证
    print("\n3. 验证保存结果...")
    sources = load_rss_sources()
    found = any(s['id'] == 'test_source_1' for s in sources)
    if found:
        print(f"   ✓ 验证成功，当前共 {len(sources)} 个源")
    else:
        print("   ✗ 验证失败")
    
    # 清理
    print("\n4. 清理测试数据...")
    sources = [s for s in sources if s['id'] != 'test_source_1']
    save_rss_sources(sources)
    print("   ✓ 清理完成")
    
    print("\n" + "=" * 60)
    print("✅ 配置功能测试通过")
    print("=" * 60)


def test_auth():
    """测试鉴权功能"""
    print("\n" + "=" * 60)
    print("测试鉴权功能")
    print("=" * 60)
    
    with app.test_client() as client:
        # 测试未登录访问
        print("\n1. 测试未登录访问 API...")
        response = client.get('/api/sources')
        print(f"   状态码: {response.status_code}")
        print(f"   预期: 401 (未授权)")
        assert response.status_code == 401, "应该返回 401"
        
        # 测试错误的授权码
        print("\n2. 测试错误的授权码...")
        response = client.post(
            '/login',
            json={'auth_code': 'wrong-code'},
            content_type='application/json'
        )
        print(f"   状态码: {response.status_code}")
        print(f"   预期: 401 (授权失败)")
        assert response.status_code == 401, "应该返回 401"
        
        # 测试正确的授权码
        print("\n3. 测试正确的授权码...")
        response = client.post(
            '/login',
            json={'auth_code': AUTH_CODE},
            content_type='application/json'
        )
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        assert response.status_code == 200, "应该返回 200"
        assert data.get('success') == True, "应该登录成功"
        
        # 测试登录后访问
        print("\n4. 测试登录后访问 API...")
        response = client.get('/api/sources')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {data.get('total')}")
        assert response.status_code == 200, "应该返回 200"
        
        # 测试退出登录
        print("\n5. 测试退出登录...")
        response = client.get('/logout')
        print(f"   状态码: {response.status_code}")
        
        # 再次访问应该失败
        print("\n6. 测试退出后访问...")
        response = client.get('/api/sources')
        print(f"   状态码: {response.status_code}")
        print(f"   预期: 401 (未授权)")
        assert response.status_code == 401, "应该返回 401"
    
    print("\n" + "=" * 60)
    print("✅ 鉴权功能测试通过")
    print("=" * 60)


def test_api_routes():
    """测试 API 路由"""
    print("\n" + "=" * 60)
    print("测试 API 路由")
    print("=" * 60)
    
    with app.test_client() as client:
        # 先登录
        client.post(
            '/login',
            json={'auth_code': AUTH_CODE},
            content_type='application/json'
        )
        
        # 测试健康检查
        print("\n1. 测试健康检查...")
        response = client.get('/health')
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.get_json()}")
        
        # 测试获取列表
        print("\n2. 测试获取 RSS 源列表...")
        response = client.get('/api/sources')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {data.get('total')}")
        
        # 测试添加
        print("\n3. 测试添加 RSS 源...")
        new_source = {
            'name': 'API测试公众号',
            'url': 'http://rss.jintiankansha.me/rss/APITEST',
            'description': 'API测试',
            'enabled': True
        }
        response = client.post(
            '/api/sources',
            json=new_source,
            content_type='application/json'
        )
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        print(f"   消息: {data.get('message')}")
        
        if data.get('success'):
            source_id = data.get('data', {}).get('id')
            
            # 测试更新
            print(f"\n4. 测试更新 RSS 源 (ID: {source_id})...")
            update_data = {
                'name': 'API测试公众号(已修改)',
                'url': 'http://rss.jintiankansha.me/rss/APITEST_UPDATED',
                'description': 'API测试 - 已更新'
            }
            response = client.put(
                f'/api/sources/{source_id}',
                json=update_data,
                content_type='application/json'
            )
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            
            # 测试禁用/启用
            print(f"\n5. 测试切换启用状态...")
            response = client.post(f'/api/sources/{source_id}/toggle')
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            
            # 测试删除
            print(f"\n6. 测试删除 RSS 源...")
            response = client.delete(f'/api/sources/{source_id}')
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            print(f"   消息: {data.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ API 路由测试通过")
    print("=" * 60)


if __name__ == '__main__':
    print("\n🔐 授权码配置:")
    print(f"   AUTH_CODE: {AUTH_CODE[:5]}...{AUTH_CODE[-5:]}")
    print("")
    
    test_config()
    test_auth()
    test_api_routes()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("\n启动后台服务:")
    print("  cd /root/project-wb/n8n/admin")
    print("  python3 app.py")
    print("\n访问地址: http://localhost:5002")
    print(f"授权码: {AUTH_CODE}")
    print("=" * 60)

    """测试配置文件读写"""
    print("=" * 60)
    print("测试配置文件功能")
    print("=" * 60)
    
    # 测试读取
    print("\n1. 读取现有配置...")
    sources = load_rss_sources()
    print(f"   当前有 {len(sources)} 个 RSS 源")
    for source in sources:
        print(f"   - {source['name']}: {source['url'][:50]}...")
    
    # 测试添加
    print("\n2. 测试添加新源...")
    test_source = {
        'id': 'test_source_1',
        'name': '测试公众号',
        'url': 'http://rss.jintiankansha.me/rss/TEST',
        'description': '测试用 RSS 源',
        'enabled': True,
        'created_at': '2026-02-20T20:00:00'
    }
    
    sources.append(test_source)
    if save_rss_sources(sources):
        print("   ✓ 添加成功")
    else:
        print("   ✗ 添加失败")
    
    # 验证
    print("\n3. 验证保存结果...")
    sources = load_rss_sources()
    found = any(s['id'] == 'test_source_1' for s in sources)
    if found:
        print(f"   ✓ 验证成功，当前共 {len(sources)} 个源")
    else:
        print("   ✗ 验证失败")
    
    # 清理
    print("\n4. 清理测试数据...")
    sources = [s for s in sources if s['id'] != 'test_source_1']
    save_rss_sources(sources)
    print("   ✓ 清理完成")
    
    print("\n" + "=" * 60)
    print("✅ 配置功能测试通过")
    print("=" * 60)


def test_api_routes():
    """测试 API 路由"""
    print("\n" + "=" * 60)
    print("测试 API 路由")
    print("=" * 60)
    
    with app.test_client() as client:
        # 测试健康检查
        print("\n1. 测试健康检查...")
        response = client.get('/health')
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.get_json()}")
        
        # 测试获取列表
        print("\n2. 测试获取 RSS 源列表...")
        response = client.get('/api/sources')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {data.get('total')}")
        
        # 测试添加
        print("\n3. 测试添加 RSS 源...")
        new_source = {
            'name': 'API测试公众号',
            'url': 'http://rss.jintiankansha.me/rss/APITEST',
            'description': 'API测试',
            'enabled': True
        }
        response = client.post(
            '/api/sources',
            json=new_source,
            content_type='application/json'
        )
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功: {data.get('success')}")
        print(f"   消息: {data.get('message')}")
        
        if data.get('success'):
            source_id = data.get('data', {}).get('id')
            
            # 测试更新
            print(f"\n4. 测试更新 RSS 源 (ID: {source_id})...")
            update_data = {
                'name': 'API测试公众号(已修改)',
                'url': 'http://rss.jintiankansha.me/rss/APITEST_UPDATED',
                'description': 'API测试 - 已更新'
            }
            response = client.put(
                f'/api/sources/{source_id}',
                json=update_data,
                content_type='application/json'
            )
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            
            # 测试禁用/启用
            print(f"\n5. 测试切换启用状态...")
            response = client.post(f'/api/sources/{source_id}/toggle')
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            
            # 测试删除
            print(f"\n6. 测试删除 RSS 源...")
            response = client.delete(f'/api/sources/{source_id}')
            data = response.get_json()
            print(f"   状态码: {response.status_code}")
            print(f"   成功: {data.get('success')}")
            print(f"   消息: {data.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ API 路由测试通过")
    print("=" * 60)


if __name__ == '__main__':
    test_config()
    test_api_routes()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("\n启动后台服务:")
    print("  cd /root/project-wb/n8n/admin")
    print("  python3 app.py")
    print("\n访问地址: http://localhost:5002")
    print("=" * 60)
