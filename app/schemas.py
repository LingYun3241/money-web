"""请求与响应模型。"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Category


class RecordCreate(BaseModel):
    """添加账目请求。"""

    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category: Category
    record_date: date
    note: str = Field(default="", max_length=255)

    @field_validator("amount")
    @classmethod
    def check_amount_scale(cls, value: Decimal) -> Decimal:
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -2:
            raise ValueError("金额最多两位小数")
        return value


class RecordOut(BaseModel):
    """账目响应；金额固定为字符串，避免浮点误差。"""

    id: int
    amount: str
    category: Category
    record_date: date
    note: str
    created_at: datetime


class CategoryStat(BaseModel):
    """单个分类的支出汇总。"""

    category: Category
    amount: str


class StatisticsOut(BaseModel):
    """分类统计响应；金额固定为字符串。"""

    total_amount: str
    total_count: int
    categories: list[CategoryStat]
