# API - 收藏 & 消息
from flask import Blueprint, request, jsonify
from models.database import get_db
import json

interact_bp = Blueprint('interact', __name__)

# ===== 收藏 =====

@interact_bp.route('/favorite/toggle', methods=['POST'])
def toggle_favorite():
    data = request.json
    user_id = data.get('user_id')
    goods_id = data.get('goods_id')
    
    if not user_id or not goods_id:
        return jsonify({'ok': False, 'message': '参数错误'})
    
    db = get_db()
    fav = db.execute(
        "SELECT id FROM favorites WHERE user_id=? AND goods_id=?",
        (user_id, goods_id)
    ).fetchone()
    
    if fav:
        db.execute("DELETE FROM favorites WHERE id=?", (fav['id'],))
        db.execute("UPDATE goods SET likes = MAX(0, likes - 1) WHERE id=?", (goods_id,))
        action = 'removed'
    else:
        db.execute("INSERT INTO favorites (user_id, goods_id) VALUES (?, ?)", (user_id, goods_id))
        db.execute("UPDATE goods SET likes = likes + 1 WHERE id=?", (goods_id,))
        action = 'added'
    
    db.commit()
    return jsonify({'ok': True, 'action': action, 'favorited': action == 'added'})

@interact_bp.route('/favorite/list', methods=['GET'])
def favorite_list():
    """我的收藏"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'message': '缺少用户ID'})
    
    db = get_db()
    goods = db.execute('''
        SELECT g.*, u.nickname, u.avatar, c.name as category_name
        FROM favorites f
        JOIN goods g ON f.goods_id = g.id
        JOIN users u ON g.user_id = u.id
        LEFT JOIN categories c ON g.category_id = c.id
        WHERE f.user_id=? AND g.status='on_sale'
        ORDER BY f.created_at DESC
    ''', (user_id,)).fetchall()
    
    result = []
    for g in goods:
        item = dict(g)
        item['images'] = json.loads(g['images']) if isinstance(g['images'], str) else []
        item['price'] = float(g['price'])
        result.append(item)
    
    return jsonify({'ok': True, 'goods': result})

# ===== 消息 =====

@interact_bp.route('/message/send', methods=['POST'])
def send_message():
    data = request.json
    from_user = data.get('from_user_id')
    to_user = data.get('to_user_id')
    goods_id = data.get('goods_id', 0)
    content = data.get('content', '')
    
    if not all([from_user, to_user, content]):
        return jsonify({'ok': False, 'message': '参数错误'})
    
    db = get_db()
    db.execute(
        "INSERT INTO messages (from_user_id, to_user_id, goods_id, content) VALUES (?, ?, ?, ?)",
        (from_user, to_user, goods_id, content)
    )
    db.commit()
    return jsonify({'ok': True, 'message': '发送成功'})

@interact_bp.route('/message/list', methods=['GET'])
def get_messages():
    """获取消息列表"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'message': '缺少用户ID'})
    
    db = get_db()
    msgs = db.execute('''
        SELECT m.*, u.nickname, u.avatar 
        FROM messages m
        JOIN users u ON (CASE WHEN m.from_user_id=? THEN m.to_user_id ELSE m.from_user_id END) = u.id
        WHERE m.from_user_id=? OR m.to_user_id=?
        ORDER BY m.created_at DESC
        LIMIT 50
    ''', (user_id, user_id, user_id)).fetchall()
    
    return jsonify({'ok': True, 'messages': [dict(m) for m in msgs]})

@interact_bp.route('/message/read', methods=['POST'])
def mark_read():
    data = request.json
    user_id = data.get('user_id')
    goods_id = data.get('goods_id', 0)
    
    db = get_db()
    if goods_id:
        db.execute("UPDATE messages SET is_read=1 WHERE to_user_id=? AND goods_id=?", (user_id, goods_id))
    else:
        db.execute("UPDATE messages SET is_read=1 WHERE to_user_id=?", (user_id,))
    db.commit()
    return jsonify({'ok': True})
