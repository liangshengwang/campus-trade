# API - 商品相关接口
from flask import Blueprint, request, jsonify
from models.database import get_db
import json
import os

goods_bp = Blueprint('goods', __name__)

@goods_bp.route('/list', methods=['GET'])
def get_goods_list():
    """获取商品列表（首页）"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    sort = request.args.get('sort', 'latest')  # latest/price_asc/price_desc
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    offset = (page - 1) * size
    
    db = get_db()
    where = ["g.status='on_sale'"]
    params = []
    
    if category:
        where.append("g.category_id=?")
        params.append(category)
    if keyword:
        where.append("(g.title LIKE ? OR g.description LIKE ?)")
        kw = f'%{keyword}%'
        params.extend([kw, kw])
    
    # 排序
    order_map = {
        'latest': 'g.created_at DESC',
        'price_asc': 'g.price ASC',
        'price_desc': 'g.price DESC',
        'popular': 'g.views DESC',
    }
    order_by = order_map.get(sort, 'g.created_at DESC')
    
    query = f'''
        SELECT g.*, u.nickname, u.avatar, u.student_id,
               c.name as category_name
        FROM goods g
        JOIN users u ON g.user_id = u.id
        LEFT JOIN categories c ON g.category_id = c.id
        WHERE {' AND '.join(where)}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    '''
    params.extend([size, offset])
    
    goods = db.execute(query, params).fetchall()
    
    # 总数
    count_query = f'''
        SELECT COUNT(*) as total FROM goods g 
        WHERE {' AND '.join(where)}
    '''
    total = db.execute(count_query, params[:-2]).fetchone()['total'] if params else 0
    
    result = []
    for g in goods:
        item = dict(g)
        item['images'] = json.loads(g['images']) if isinstance(g['images'], str) else g.get('images', '[]')
        item['price'] = float(g['price'])
        item['original_price'] = float(g['original_price']) if g['original_price'] else 0
        result.append(item)
    
    return jsonify({
        'ok': True,
        'goods': result,
        'total': total,
        'page': page,
        'has_more': len(result) >= size
    })

@goods_bp.route('/detail', methods=['GET'])
def get_goods_detail():
    """商品详情"""
    goods_id = request.args.get('id')
    if not goods_id:
        return jsonify({'ok': False, 'message': '缺少商品ID'})
    
    db = get_db()
    db.execute("UPDATE goods SET views = views + 1 WHERE id=?", (goods_id,))
    
    goods = db.execute('''
        SELECT g.*, u.nickname, u.avatar, u.student_id, u.credit, u.wechat, u.phone,
               c.name as category_name
        FROM goods g
        JOIN users u ON g.user_id = u.id
        LEFT JOIN categories c ON g.category_id = c.id
        WHERE g.id=?
    ''', (goods_id,)).fetchone()
    
    if not goods:
        return jsonify({'ok': False, 'message': '商品不存在'})
    
    result = dict(goods)
    result['images'] = json.loads(goods['images']) if isinstance(goods['images'], str) else goods.get('images', '[]')
    result['price'] = float(goods['price'])
    result['original_price'] = float(goods['original_price']) if goods['original_price'] else 0
    db.commit()
    
    return jsonify({'ok': True, 'goods': result})

@goods_bp.route('/publish', methods=['POST'])
def publish_goods():
    """发布商品"""
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'message': '请先登录'})
    
    title = data.get('title', '').strip()
    if not title or len(title) < 2:
        return jsonify({'ok': False, 'message': '标题至少2个字'})
    
    price = float(data.get('price', 0))
    if price <= 0:
        return jsonify({'ok': False, 'message': '请输入有效价格'})
    
    db = get_db()
    c = db.execute('''
        INSERT INTO goods (user_id, category_id, title, description, price, 
                          original_price, images, is_negotiable, condition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get('category_id', 9),
        title,
        data.get('description', ''),
        price,
        float(data.get('original_price', 0)),
        json.dumps(data.get('images', [])),
        1 if data.get('is_negotiable', True) else 0,
        data.get('condition', 'used'),
    ))
    db.commit()
    
    return jsonify({
        'ok': True, 
        'goods_id': c.lastrowid,
        'message': '发布成功！'
    })

@goods_bp.route('/update', methods=['POST'])
def update_goods():
    data = request.json
    goods_id = data.get('goods_id')
    user_id = data.get('user_id')
    
    if not goods_id or not user_id:
        return jsonify({'ok': False, 'message': '参数错误'})
    
    db = get_db()
    goods = db.execute("SELECT * FROM goods WHERE id=? AND user_id=?", (goods_id, user_id)).fetchone()
    if not goods:
        return jsonify({'ok': False, 'message': '无权操作'})
    
    fields = ['title', 'description', 'price', 'category_id', 'images', 'is_negotiable', 'condition']
    updates = {k: data[k] for k in fields if k in data}
    
    if updates:
        # 处理特殊字段
        if 'images' in updates and isinstance(updates['images'], list):
            updates['images'] = json.dumps(updates['images'])
        
        set_clause = ', '.join(f"{k}=?" for k in updates.keys())
        values = list(updates.values()) + [goods_id]
        db.execute(f"UPDATE goods SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
        db.commit()
    
    return jsonify({'ok': True, 'message': '更新成功'})

@goods_bp.route('/mine', methods=['GET'])
def my_goods():
    """我发布的商品"""
    user_id = request.args.get('user_id')
    status = request.args.get('status', '')  # on_sale/sold/all
    
    if not user_id:
        return jsonify({'ok': False, 'message': '缺少用户ID'})
    
    db = get_db()
    where = ["g.user_id=?"]
    params = [user_id]
    
    if status and status != 'all':
        where.append("g.status=?")
        params.append(status)
    
    goods = db.execute(f'''
        SELECT g.*, c.name as category_name
        FROM goods g
        LEFT JOIN categories c ON g.category_id = c.id
        WHERE {' AND '.join(where)}
        ORDER BY g.created_at DESC
    ''', params).fetchall()
    
    result = []
    for g in goods:
        item = dict(g)
        item['images'] = json.loads(g['images']) if isinstance(g['images'], str) else []
        item['price'] = float(g['price'])
        result.append(item)
    
    return jsonify({'ok': True, 'goods': result})

@goods_bp.route('/categories', methods=['GET'])
def get_categories():
    db = get_db()
    cats = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    return jsonify({'ok': True, 'categories': [dict(c) for c in cats]})

@goods_bp.route('/mark_sold', methods=['POST'])
def mark_sold():
    """标记商品为已售"""
    data = request.json
    goods_id = data.get('goods_id')
    user_id = data.get('user_id')
    
    if not goods_id or not user_id:
        return jsonify({'ok': False, 'message': '参数错误'})
    
    db = get_db()
    goods = db.execute("SELECT * FROM goods WHERE id=? AND user_id=?", (goods_id, user_id)).fetchone()
    if not goods:
        return jsonify({'ok': False, 'message': '无权操作'})
    
    db.execute("UPDATE goods SET status='sold', updated_at=CURRENT_TIMESTAMP WHERE id=?", (goods_id,))
    db.commit()
    return jsonify({'ok': True, 'message': '已标记为已售'})

@goods_bp.route('/delete', methods=['POST'])
def delete_goods():
    data = request.json
    goods_id = data.get('goods_id')
    user_id = data.get('user_id')
    
    db = get_db()
    goods = db.execute("SELECT * FROM goods WHERE id=? AND user_id=?", (goods_id, user_id)).fetchone()
    if not goods:
        return jsonify({'ok': False, 'message': '无权操作'})
    
    db.execute("DELETE FROM goods WHERE id=?", (goods_id,))
    db.execute("DELETE FROM favorites WHERE goods_id=?", (goods_id,))
    db.commit()
    
    return jsonify({'ok': True, 'message': '删除成功'})
