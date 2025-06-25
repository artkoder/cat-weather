import sqlite3
from typing import Optional


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS superadmins(
                user_id INTEGER PRIMARY KEY,
                tz_offset INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS channels(
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def set_timezone(self, user_id: int, offset: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO superadmins(user_id, tz_offset) VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET tz_offset=excluded.tz_offset
            """,
            (user_id, offset),
        )
        self.conn.commit()

    def get_timezone(self, user_id: int) -> Optional[int]:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT tz_offset FROM superadmins WHERE user_id=?", (user_id,)
        ).fetchone()
        return row["tz_offset"] if row else None

    def add_channel(self, chat_id: int, title: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO channels(chat_id, title) VALUES(?, ?)",
            (chat_id, title),
        )
        self.conn.commit()

    def remove_channel(self, chat_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM channels WHERE chat_id=?", (chat_id,))
        self.conn.commit()
