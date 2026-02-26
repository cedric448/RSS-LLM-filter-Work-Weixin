#!/usr/bin/env python3
"""
RSS 源配置后台管理系统
提供 Web 界面管理"今天看点啥"公众号 RSS 订阅
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rss-admin-secret-key-2026')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session 有效期 24 小时

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'rss-sources.json')

# 鉴权配置
AUTH_CODE = os.environ.get('RSS_ADMIN_AUTH_CODE', 'eID6g1ka71A-p7UVNgwpBRnIIjXiOvPp')


def require_auth(f):
    """鉴权装饰器 - 要求用户已登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                # API 请求返回 JSON 错误
                return jsonify({
                    'success': False,
                    'message': '未授权访问，请先登录',
                    'error': 'unauthorized'
                }), 401
            else:
                # 页面请求重定向到登录页
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def load_rss_sources() -> List[Dict]:
    """加载 RSS 源配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('sources', [])
    except FileNotFoundError:
        return []


def save_rss_sources(sources: List[Dict]) -> bool:
    """保存 RSS 源配置"""
    try:
        data = {
            'sources': sources,
            'total': len(sources),
            'updated_at': datetime.now().isoformat()
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


@app.route('/login', methods=['GET'])
def login():
    """登录页面"""
    # 如果已登录，重定向到首页
    if session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def do_login():
    """处理登录请求"""
    data = request.get_json() if request.is_json else request.form
    auth_code = data.get('auth_code', '').strip()
    
    if auth_code == AUTH_CODE:
        session['authenticated'] = True
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True  # 使用永久 session
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        else:
            return redirect(url_for('index'))
    else:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': '授权码错误'
            }), 401
        else:
            return render_template('login.html', error='授权码错误')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@require_auth
def index():
    """首页 - RSS 源列表"""
    sources = load_rss_sources()
    return render_template('index.html', sources=sources)


@app.route('/api/sources', methods=['GET'])
@require_auth
def get_sources():
    """API: 获取所有 RSS 源"""
    sources = load_rss_sources()
    return jsonify({
        'success': True,
        'data': sources,
        'total': len(sources)
    })


@app.route('/api/sources', methods=['POST'])
@require_auth
def add_source():
    """API: 添加新的 RSS 源"""
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('name') or not data.get('url'):
        return jsonify({
            'success': False,
            'message': '公众号名称和 RSS 链接不能为空'
        }), 400
    
    # 验证 slug 字段(必填)
    if not data.get('slug') or not data.get('slug').strip():
        return jsonify({
            'success': False,
            'message': 'Slug 不能为空'
        }), 400
    
    sources = load_rss_sources()
    
    # 检查 slug 是否重复
    slug = data['slug'].strip()
    if any(s.get('slug') == slug for s in sources):
        return jsonify({
            'success': False,
            'message': f'Slug "{slug}" 已存在,请使用不同的 slug'
        }), 400
    
    # 生成新的 ID
    max_id = 0
    for source in sources:
        source_id = source.get('id', 'source_0')
        try:
            num = int(source_id.split('_')[1])
            max_id = max(max_id, num)
        except:
            pass
    
    new_source = {
        'id': f'source_{max_id + 1}',
        'name': data['name'].strip(),
        'url': data['url'].strip(),
        'slug': slug,
        'description': data.get('description', '').strip(),
        'enabled': data.get('enabled', True),
        'created_at': datetime.now().isoformat()
    }
    
    sources.append(new_source)
    
    if save_rss_sources(sources):
        return jsonify({
            'success': True,
            'message': '添加成功',
            'data': new_source
        })
    else:
        return jsonify({
            'success': False,
            'message': '保存失败'
        }), 500


@app.route('/api/sources/<source_id>', methods=['PUT'])
@require_auth
def update_source(source_id):
    """API: 更新 RSS 源"""
    data = request.get_json()
    sources = load_rss_sources()
    
    # 如果提供了 slug,检查是否与其他源重复
    new_slug = data.get('slug', '').strip()
    if new_slug:
        for source in sources:
            if source['id'] != source_id and source.get('slug') == new_slug:
                return jsonify({
                    'success': False,
                    'message': f'Slug "{new_slug}" 已被其他源使用'
                }), 400
    
    # 查找并更新
    found = False
    for source in sources:
        if source['id'] == source_id:
            source['name'] = data.get('name', source['name']).strip()
            source['url'] = data.get('url', source['url']).strip()
            source['description'] = data.get('description', source.get('description', '')).strip()
            source['enabled'] = data.get('enabled', source.get('enabled', True))
            
            # 更新 slug (如果提供)
            if new_slug:
                source['slug'] = new_slug
            
            source['updated_at'] = datetime.now().isoformat()
            found = True
            break
    
    if not found:
        return jsonify({
            'success': False,
            'message': 'RSS 源不存在'
        }), 404
    
    if save_rss_sources(sources):
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '保存失败'
        }), 500


@app.route('/api/sources/<source_id>', methods=['DELETE'])
@require_auth
def delete_source(source_id):
    """API: 删除 RSS 源"""
    sources = load_rss_sources()
    
    # 过滤掉要删除的源
    new_sources = [s for s in sources if s['id'] != source_id]
    
    if len(new_sources) == len(sources):
        return jsonify({
            'success': False,
            'message': 'RSS 源不存在'
        }), 404
    
    if save_rss_sources(new_sources):
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '保存失败'
        }), 500


@app.route('/api/sources/<source_id>/toggle', methods=['POST'])
@require_auth
def toggle_source(source_id):
    """API: 启用/禁用 RSS 源"""
    sources = load_rss_sources()
    
    found = False
    for source in sources:
        if source['id'] == source_id:
            source['enabled'] = not source.get('enabled', True)
            source['updated_at'] = datetime.now().isoformat()
            found = True
            break
    
    if not found:
        return jsonify({
            'success': False,
            'message': 'RSS 源不存在'
        }), 404
    
    if save_rss_sources(sources):
        return jsonify({
            'success': True,
            'message': '操作成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '保存失败'
        }), 500


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # 开发环境运行
    app.run(host='0.0.0.0', port=5002, debug=True)
