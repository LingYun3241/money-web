"""账目接口：添加、列表、删除与分类统计。"""

from decimal import Decimal

import pymysql
from fastapi import APIRouter, HTTPException, Response, status

from app.db import get_cursor
from app.models import CATEGORIES
from app.schemas import CategoryStat, RecordCreate, RecordOut, StatisticsOut

router = APIRouter(prefix="/api", tags=["records"])


def _to_out(row: dict) -> RecordOut:
    return RecordOut(
        id=row["id"],
        amount=str(row["amount"]),
        category=row["category"],
        record_date=row["record_date"],
        note=row["note"],
        created_at=row["created_at"],
    )


def _money(value) -> str:
    """把 SUM 结果统一格式化为两位小数字符串。"""
    if value is None:
        value = Decimal("0")
    elif not isinstance(value, Decimal):
        value = Decimal(str(value))
    return format(value.quantize(Decimal("0.01")), "f")


@router.post("/records", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(payload: RecordCreate):
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO records (amount, category, record_date, note) "
                "VALUES (%s, %s, %s, %s)",
                (payload.amount, payload.category, payload.record_date, payload.note),
            )
            record_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, amount, category, record_date, note, created_at "
                "FROM records WHERE id = %s",
                (record_id,),
            )
            row = cursor.fetchone()
    except pymysql.err.MySQLError:
        raise HTTPException(status_code=500, detail="数据库操作失败") from None

    if row is None:
        raise HTTPException(status_code=500, detail="写入后读取失败")
    return _to_out(row)


@router.get("/records", response_model=list[RecordOut])
def list_records():
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id, amount, category, record_date, note, created_at "
                "FROM records ORDER BY record_date DESC, id DESC"
            )
            rows = cursor.fetchall()
    except pymysql.err.MySQLError:
        raise HTTPException(status_code=500, detail="数据库操作失败") from None

    return [_to_out(row) for row in rows]


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int):
    try:
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM records WHERE id = %s", (record_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="记录不存在")
    except pymysql.err.MySQLError:
        raise HTTPException(status_code=500, detail="数据库操作失败") from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/statistics", response_model=StatisticsOut)
def get_statistics():
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT category, SUM(amount) AS amount "
                "FROM records GROUP BY category"
            )
            category_rows = cursor.fetchall()

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total_amount, COUNT(*) AS total_count "
                "FROM records"
            )
            totals = cursor.fetchone()
    except pymysql.err.MySQLError:
        raise HTTPException(status_code=500, detail="数据库操作失败") from None

    by_category = {row["category"]: row["amount"] for row in category_rows}
    categories = [
        CategoryStat(category=category, amount=_money(by_category.get(category)))
        for category in CATEGORIES
    ]

    return StatisticsOut(
        total_amount=_money(totals["total_amount"]),
        total_count=totals["total_count"],
        categories=categories,
    )
