"""pytest 共享配置：使用独立测试库与专用测试账号，禁止触碰开发库。"""

import os
from pathlib import Path

import pymysql
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TEST_DB_NAME = "expense_tracker_test"
TEST_DB_USER = os.getenv("TEST_DB_USER", "expense_test")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "")

if not TEST_DB_PASSWORD:
    raise RuntimeError("缺少 TEST_DB_PASSWORD，请在 .env 中配置专用测试账号")

# 必须在导入 app 之前覆盖，确保被测应用使用测试库和测试账号。
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["DB_USER"] = TEST_DB_USER
os.environ["DB_PASSWORD"] = TEST_DB_PASSWORD

from app import config  # noqa: E402
from app.main import app  # noqa: E402


def _connect(database: str | None) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=database,
        charset=config.DB_CHARSET,
        connect_timeout=5,
        autocommit=True,
    )


def _assert_test_database(cursor) -> None:
    cursor.execute("SELECT DATABASE() AS current_db")
    current = cursor.fetchone()[0]
    if current != TEST_DB_NAME:
        raise RuntimeError(f"拒绝操作非测试库：{current!r}")


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    if config.DB_NAME != TEST_DB_NAME:
        pytest.fail(f"测试库配置错误：{config.DB_NAME!r}")
    if config.DB_USER != TEST_DB_USER:
        pytest.fail("测试账号配置错误")

    conn = _connect(database=TEST_DB_NAME)
    try:
        with conn.cursor() as cursor:
            _assert_test_database(cursor)
            cursor.execute("SELECT COUNT(*) FROM records")
            cursor.fetchone()
    except pymysql.err.MySQLError as exc:
        code = exc.args[0] if exc.args else "unknown"
        pytest.fail(
            "测试库或 records 表不可用；请由管理员预先创建 "
            f"{TEST_DB_NAME}.records，并确认测试账号有 SELECT/INSERT/DELETE 权限（错误码 {code}）"
        )
    finally:
        conn.close()

    yield


def _clear_test_records() -> None:
    """只清空专用测试库中的记录，逐条按主键删除并先校验当前库。"""
    conn = _connect(database=TEST_DB_NAME)
    try:
        with conn.cursor() as cursor:
            _assert_test_database(cursor)
            cursor.execute("SELECT id FROM records")
            record_ids = [row[0] for row in cursor.fetchall()]
            for record_id in record_ids:
                cursor.execute("DELETE FROM records WHERE id = %s", (record_id,))
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_test_records():
    _clear_test_records()
    yield
    _clear_test_records()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
