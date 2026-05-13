#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校园二手交易系统 - 后端服务器
Flask + SQLite
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend')
CORS(app)

from api.user import user_bp
from api.goods import goods_bp
from api.interact import interact_bp

app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(goods_bp, url_prefix='/api/goods')
app.register_blueprint(interact_bp, url_prefix='/api/interact')

# 上传文件访问
uploads_dir = os.path.join(os.path.dirname(__file__), '../uploads')
os.makedirs(uploads_dir, exist_ok=True)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(uploads_dir, filename)

from models.database import init_db
init_db()

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    from flask import request
    import uuid
    file = request.files.get('file')
    if not file:
        return {'ok': False, 'message': '请选择文件'}
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        return {'ok': False, 'message': '不支持的图片格式'}
    upload_dir = os.path.join(os.path.dirname(__file__), '../uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    url = f"/uploads/{filename}"
    return {'ok': True, 'url': url}

if __name__ == '__main__':
    print("=" * 50)
    print("  校园二手交易系统")
    print("  端口: http://127.0.0.1:18800")
    print("=" * 50)
    app.run(host='127.0.0.1', port=18800, debug=False)
