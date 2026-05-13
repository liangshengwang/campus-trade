# API - 用户相关接口
from flask import Blueprint, request, jsonify
from models.database import get_db
import json

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    """微信登录 / 学号登录"""
    data = request.json
    student_id = data.get('student_id', '').strip()
    code = data.get('code', '')  # 微信登录 code
    
    if not student_id:
        # 微信登录模式
        return jsonify({
            'ok': False,
            'message': '请先验证学号'
        })
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE student_id = ?", (student_id,)).fetchone()
    
    if user:
        # 已有用户，更新信息
        nickname = data.get('nickname', user['nickname'])
        avatar = data.get('avatar', user['avatar'])
        db.execute("UPDATE users SET nickname=?, avatar=? WHERE id=?", 
                   (nickname, avatar, user['id']))
    else:
        # 新用户
        nickname = data.get('nickname', f'同学{student_id[-4:]}')
        avatar = data.get('avatar', '')
        c = db.execute(
            "INSERT INTO users (student_id, nickname, avatar) VALUES (?, ?, ?)",
            (student_id, nickname, avatar)
        )
        user_id = c.lastrowid
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    
    db.commit()
    return jsonify({
        'ok': True,
        'user': dict(user)
    })

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'message': '缺少用户ID'})
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        return jsonify({'ok': False, 'message': '用户不存在'})
    
    # 统计
    selling = db.execute("SELECT COUNT(*) as c FROM goods WHERE user_id=? AND status='on_sale'", (user_id,)).fetchone()['c']
    sold = db.execute("SELECT COUNT(*) as c FROM goods WHERE user_id=? AND status='sold'", (user_id,)).fetchone()['c']
    
    result = dict(user)
    result['selling_count'] = selling
    result['sold_count'] = sold
    return jsonify({'ok': True, 'user': result})

@user_bp.route('/update', methods=['POST'])
def update_profile():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'message': '缺少用户ID'})
    
    db = get_db()
    fields = ['nickname', 'phone', 'wechat', 'school', 'major', 'avatar']
    updates = {k: data[k] for k in fields if k in data and data[k]}
    
    if updates:
        set_clause = ', '.join(f"{k}=?" for k in updates.keys())
        values = list(updates.values()) + [user_id]
        db.execute(f"UPDATE users SET {set_clause} WHERE id=?", values)
        db.commit()
    
    return jsonify({'ok': True, 'message': '更新成功'})
