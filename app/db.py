"""数据库访问层：PyMySQL 同步驱动，每次调用独立连接，不共享全局连接。"""

from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from app import config

CONNECT_TIMEOUT_SECONDS = 5


def _connect() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset=config.DB_CHARSET,
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        read_timeout=CONNECT_TIMEOUT_SECONDS,
        write_timeout=CONNECT_TIMEOUT_SECONDS,
        autocommit=False,
    )


@contextmanager
def get_cursor() -> Iterator[DictCursor]:
    """每次调用创建独立连接；正常结束提交，异常回滚，最终关闭游标与连接。"""
    conn = _connect()
    cursor = None
    try:
        cursor = conn.cursor(DictCursor)
        yield cursor
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def check_database() -> str:
    """返回 ok / not_configured / mysql_unavailable / auth_failed / database_missing / timeout / error。"""
    if not config.DB_NAME or not config.DB_USER:
        return "not_configured"

    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            cursor.fetchone()
    except pymysql.err.OperationalError as exc:
        return _classify_operational_error(exc)
    except Exception:
        return "error"
    return "ok"


def _classify_operational_error(exc: pymysql.err.OperationalError) -> str:
    code = exc.args[0] if exc.args else None
    message = str(exc).lower()

    if code in (1044, 1045):
        return "auth_failed"
    if code == 1049:
        return "database_missing"

    is_timeout = (
        "timed out" in message
        or isinstance(exc.__cause__, TimeoutError)
        or isinstance(exc.__context__, TimeoutError)
    )
    if is_timeout:
        return "timeout"

    if code in (2002, 2003, 2013):
        return "mysql_unavailable"

    return "error"
