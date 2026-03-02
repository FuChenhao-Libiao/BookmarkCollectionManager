# 数据库操作模块

import sqlite3
import os
from config import DATABASE_PATH


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典格式
    return conn


def init_database():
    """初始化数据库，创建表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS music_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            style TEXT DEFAULT '',
            duration INTEGER DEFAULT 10,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            temperature REAL DEFAULT 1.0,
            top_k INTEGER DEFAULT 250,
            top_p REAL DEFAULT 0.95,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def save_generation(prompt: str, style: str, duration: int, file_path: str,
                    file_size: int, temperature: float, top_k: int, top_p: float) -> int:
    """保存生成记录，返回记录 ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO music_generations (prompt, style, duration, file_path, file_size, temperature, top_k, top_p)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (prompt, style, duration, file_path, file_size, temperature, top_k, top_p))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_generation(record_id: int) -> dict:
    """根据 ID 获取生成记录"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM music_generations WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_history(page: int = 1, page_size: int = 12, style: str = None) -> dict:
    """获取生成历史（分页）"""
    conn = get_connection()
    cursor = conn.cursor()

    # 构建查询条件
    where_clause = ""
    params = []
    if style:
        where_clause = "WHERE style = ?"
        params.append(style)

    # 查询总数
    cursor.execute(f"SELECT COUNT(*) FROM music_generations {where_clause}", params)
    total = cursor.fetchone()[0]

    # 查询分页数据
    offset = (page - 1) * page_size
    cursor.execute(
        f"SELECT * FROM music_generations {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    )
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        item["file_url"] = f"/api/music/{item['id']}"
        items.append(item)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


def delete_generation(record_id: int) -> bool:
    """删除生成记录，返回是否成功"""
    conn = get_connection()
    cursor = conn.cursor()

    # 先获取文件路径
    cursor.execute("SELECT file_path FROM music_generations WHERE id = ?", (record_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    # 删除音频文件
    file_path = row["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)

    # 删除数据库记录
    cursor.execute("DELETE FROM music_generations WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return True
