"""MySQL 只读连接池，供 memory 分析使用"""
import os
from typing import Any

import aiomysql

_pool: aiomysql.Pool | None = None

_READ_PARAMS = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "db": os.getenv("MYSQL_DB", "dayagent"),
    "charset": "utf8mb4",
    "autocommit": True,
}


async def get_pool() -> aiomysql.Pool:
    """获取或创建连接池（lazy init，复用）"""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            minsize=1,
            maxsize=3,
            **_READ_PARAMS,
        )
        print(f"[MySQL] 连接池已创建: {_READ_PARAMS['host']}:{_READ_PARAMS['port']}/{_READ_PARAMS['db']}")
    return _pool


async def fetch_all(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """执行只读查询，返回字典列表"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


async def close_pool() -> None:
    """关闭连接池（应用退出时调用）"""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        print("[MySQL] 连接池已关闭")
