# 后端 - 数据库初始化
import sqlite3
import os

# DB path relative to backend directory (not models/)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campus_trade.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,      -- 学号
        nickname TEXT NOT NULL,
        avatar TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        wechat TEXT DEFAULT '',
        school TEXT DEFAULT '',
        major TEXT DEFAULT '',
        credit INTEGER DEFAULT 100,           -- 信誉分
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 商品分类
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    )''')
    
    # 商品表
    c.execute('''CREATE TABLE IF NOT EXISTS goods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER DEFAULT 0,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        price REAL NOT NULL,
        original_price REAL DEFAULT 0,
        images TEXT DEFAULT '[]',              -- JSON 数组
        status TEXT DEFAULT 'on_sale',         -- on_sale/sold/reserved
        views INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        is_negotiable INTEGER DEFAULT 1,      -- 可议价
        condition TEXT DEFAULT 'used',         -- new/used/old
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 收藏表
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goods_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, goods_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (goods_id) REFERENCES goods(id)
    )''')
    
    # 消息表
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_user_id INTEGER NOT NULL,
        goods_id INTEGER DEFAULT 0,
        content TEXT DEFAULT '',
        msg_type TEXT DEFAULT 'text',          -- text/image/system
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 初始化分类
    categories = [
        ('📚 教材教辅', 'books', 1),
        ('📱 数码产品', 'digital', 2),
        ('👕 服饰鞋包', 'fashion', 3),
        ('🏠 生活用品', 'daily', 4),
        ('🚲 交通工具', 'transport', 5),
        ('🎮 游戏娱乐', 'game', 6),
        ('🏀 运动器材', 'sports', 7),
        ('🎵 影音乐器', 'music', 8),
        ('📦 其他', 'other', 9),
    ]
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO categories (name, icon, sort_order) VALUES (?, ?, ?)", cat)
    
    conn.commit()
    conn.close()
    print("Database initialized!")

if __name__ == '__main__':
    init_db()
