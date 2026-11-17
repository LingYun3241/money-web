"""纯数据定义：分类白名单是应用内的唯一权威来源。"""

from typing import Literal, get_args

Category = Literal["餐饮", "交通", "购物", "娱乐", "居住", "其它"]

CATEGORIES: tuple[str, ...] = get_args(Category)
