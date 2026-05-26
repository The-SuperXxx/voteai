"""SQLite 数据库 - 存储问答历史"""
import sqlite3
import json
from datetime import datetime
from config import config


DB_PATH = config.DB_PATH


def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            best_answer TEXT,
            best_model TEXT,
            score REAL,
            votes TEXT,
            all_answers TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit (
            ip TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (ip, date)
        )
    """)
    conn.commit()
    conn.close()


def save_result(result_id: str, question: str, best_answer: str,
                best_model: str, score: float, votes: list,
                all_answers: list):
    """保存一次问答结果"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO questions (id, question, best_answer, best_model, score, votes, all_answers, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (result_id, question, best_answer, best_model, score,
         json.dumps(votes), json.dumps(all_answers),
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 20):
    """获取最近的问答历史"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, question, best_model, score, created_at FROM questions ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "question": r[1],
            "best_model": r[2],
            "score": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


def get_result(result_id: str):
    """获取某次问答的完整详情"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT * FROM questions WHERE id = ?", (result_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "question": row[1],
        "best_answer": row[2],
        "best_model": row[3],
        "score": row[4],
        "votes": json.loads(row[5]),
        "all_answers": json.loads(row[6]),
        "created_at": row[7],
    }


def delete_result(result_id: str):
    """删除某次问答记录"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM questions WHERE id = ?", (result_id,))
    conn.commit()
    conn.close()


FREE_LIMIT = 20


def check_and_increment(ip: str) -> dict:
    """检查IP今日剩余次数，并递增。返回 {'allowed': bool, 'remaining': int, 'limit': int}"""
    init_db()
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT count FROM rate_limit WHERE ip = ? AND date = ?",
        (ip, today)
    ).fetchone()
    if row:
        count = row[0]
        if count >= FREE_LIMIT:
            conn.close()
            return {"allowed": False, "remaining": 0, "limit": FREE_LIMIT}
        conn.execute(
            "UPDATE rate_limit SET count = count + 1 WHERE ip = ? AND date = ?",
            (ip, today)
        )
        conn.commit()
        conn.close()
        return {"allowed": True, "remaining": FREE_LIMIT - count - 1, "limit": FREE_LIMIT}
    else:
        conn.execute(
            "INSERT INTO rate_limit (ip, date, count) VALUES (?, ?, 1)",
            (ip, today)
        )
        conn.commit()
        conn.close()
        return {"allowed": True, "remaining": FREE_LIMIT - 1, "limit": FREE_LIMIT}


def get_quota(ip: str) -> dict:
    """查询IP今日剩余次数（不递增）"""
    init_db()
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT count FROM rate_limit WHERE ip = ? AND date = ?",
        (ip, today)
    ).fetchone()
    conn.close()
    used = row[0] if row else 0
    return {"remaining": max(0, FREE_LIMIT - used), "limit": FREE_LIMIT}
