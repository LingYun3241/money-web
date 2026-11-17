"""应用配置：只从环境变量或 .env 读取，不打印、不记录配置值。"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 不存在时静默跳过，由部署环境自行注入变量
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")
