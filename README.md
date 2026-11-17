# 个人支出记账（money web）

本地运行的单用户支出记账 Web 应用。第一版只做最小闭环：添加账目、查看列表、删除账目、按六个固定分类统计。

技术栈：Python + FastAPI + 同步 PyMySQL + 原生 HTML/CSS/JavaScript + 本地 MySQL。不使用 ORM、前端框架、npm 构建或 Docker。

## 环境要求

- Python 3.12（本项目在 CPython 3.12.15 上验证）
- MySQL 5.7 或更高版本，字符集使用 `utf8mb4`
- 不需要 Node.js / npm
- Windows 下命令以 Git Bash 为例；PowerShell 需把 `./.venv/Scripts/python.exe` 换成 `.\.venv\Scripts\python.exe`

## 目录结构

```text
money web/
├─ app/
│  ├─ main.py              # FastAPI 入口、静态页面、健康检查
│  ├─ config.py            # 从环境变量/.env 读取数据库配置
│  ├─ db.py                # 同步 PyMySQL 连接、事务与健康检查
│  ├─ models.py            # 六个固定分类
│  ├─ schemas.py           # Pydantic 请求/响应模型
│  └─ routers/records.py   # 账目接口
├─ static/                 # 原生前端页面、样式、脚本
├─ sql/init.sql            # 幂等建库建表脚本
├─ tests/                  # pytest 测试（独立测试库）
├─ .env.example            # 配置占位符
├─ requirements.txt
└─ README.md
```

## 安装依赖

```bash
cd "D:/develop/AI_Coding/money web"

# 创建虚拟环境（本机已验证 uv 的 CPython 3.12.15）
py -V:Astral/CPython3.12.15 -m venv .venv
# 如果系统已注册 py -3.12，也可以使用：py -3.12 -m venv .venv

# 使用清华源安装依赖
./.venv/Scripts/python.exe -m pip install -r requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

`requirements.txt` 当前包含：`fastapi`、`uvicorn[standard]`、`pymysql`、`python-dotenv`、`pytest`、`httpx`。

## 配置 `.env`

在项目根目录复制占位文件，然后填入本机 MySQL 连接信息：

```bash
cp .env.example .env
```

`.env` 的键：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=expense_tracker
DB_USER=expense_app
DB_PASSWORD=your_app_password_here
DB_CHARSET=utf8mb4
TEST_DB_USER=expense_test
TEST_DB_PASSWORD=your_test_password_here
```

说明：

- `.env` 已被 `.gitignore` 忽略，禁止提交。
- `.env.example` 只能放占位符，不能写真实密码；应包含上面的全部键，缺少 `TEST_DB_*` 时请手动补充。
- `DB_NAME` 必须与 `sql/init.sql` 中的库名一致。
- `DB_USER` / `DB_PASSWORD` 是应用专用账号，不要使用 `root`。
- `TEST_DB_USER` / `TEST_DB_PASSWORD` 只供 pytest 使用，应与应用账号使用不同密码。
- 应用只读取环境变量/`.env`，不会打印配置值。
- 不要把密码写在命令行参数、日志、截图或文档中。

## 数据库初始化

先阅读 `sql/init.sql`。脚本只包含幂等的 `CREATE DATABASE IF NOT EXISTS` 和 `CREATE TABLE IF NOT EXISTS`，不包含 `DROP`、`TRUNCATE`、`DELETE`、`ALTER`。

使用 MySQL 客户端执行（`-p` 会交互式提示输入密码，不要把密码写在命令里）：

```bash
mysql -h 127.0.0.1 -P 3306 -u <user> -p < sql/init.sql
```

也可以把脚本内容粘贴到 MySQL 客户端执行。执行前请确认连接的是本地库，且 `DB_NAME` 与脚本中的 `expense_tracker` 一致。

### 最小权限账号

应用账号只访问开发库，测试账号只访问测试库。账号主机范围仅限本机 `localhost` / `127.0.0.1`，不要使用 `%`：

```sql
-- 应用账号：开发库 records 表
CREATE USER 'expense_app'@'localhost' IDENTIFIED BY '<强密码>';
CREATE USER 'expense_app'@'127.0.0.1' IDENTIFIED BY '<强密码>';
GRANT SELECT, INSERT, DELETE ON `expense_tracker`.`records`
  TO 'expense_app'@'localhost';
GRANT SELECT, INSERT, DELETE ON `expense_tracker`.`records`
  TO 'expense_app'@'127.0.0.1';

-- 测试账号：测试库 records 表
CREATE USER 'expense_test'@'localhost' IDENTIFIED BY '<强密码>';
CREATE USER 'expense_test'@'127.0.0.1' IDENTIFIED BY '<强密码>';
GRANT SELECT, INSERT, DELETE ON `expense_tracker_test`.`records`
  TO 'expense_test'@'localhost';
GRANT SELECT, INSERT, DELETE ON `expense_tracker_test`.`records`
  TO 'expense_test'@'127.0.0.1';
```

- 不授予 `UPDATE`、DDL、`GRANT OPTION` 或账号管理权限。
- 管理员账号仅用于建库建表、建账号和授权，不写入 `.env`，也不用于日常运行。
- 测试库和 `records` 表由管理员预先创建，结构与开发库相同，库名改为 `expense_tracker_test`；测试账号不需要 `CREATE` 权限。

## 启动服务

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 --reload
```

浏览器访问：

- 页面：<http://127.0.0.1:8000/>
- 健康检查：<http://127.0.0.1:8000/api/health>
- OpenAPI 文档：<http://127.0.0.1:8000/docs>

服务只绑定 `127.0.0.1`，不要监听 `0.0.0.0`。

## API

| 方法 | 路径 | 说明 | 成功状态码 |
|---|---|---|---|
| GET | `/api/health` | 健康检查，包含数据库状态 | 200 |
| POST | `/api/records` | 添加账目 | 201 |
| GET | `/api/records` | 账目列表，按日期、ID 倒序 | 200 |
| DELETE | `/api/records/{id}` | 按主键删除账目 | 204 |
| GET | `/api/statistics` | 总额、总笔数、六分类统计 | 200 |

请求示例（金额必须是字符串）：

```json
{
  "amount": "12.50",
  "category": "餐饮",
  "record_date": "2026-11-17",
  "note": "午饭"
}
```

响应示例：

```json
{
  "id": 1,
  "amount": "12.50",
  "category": "餐饮",
  "record_date": "2026-11-17",
  "note": "午饭",
  "created_at": "2026-11-17T12:00:00"
}
```

约定：

- `amount` 必须大于 0，最多两位小数，JSON 中为字符串。
- `category` 只能是：`餐饮`、`交通`、`购物`、`娱乐`、`居住`、`其它`。
- `record_date` 为 `YYYY-MM-DD`。
- `note` 可为空，最长 255 个字符。
- 非法输入返回 422；删除不存在的记录返回 404；数据库异常返回不暴露内部细节的 500。
- 统计固定返回六个分类，没有账目的分类补 `"0.00"`。

## 测试

```bash
./.venv/Scripts/python.exe -m pytest -q
```

测试使用独立测试库 `expense_tracker_test` 和专用测试账号 `expense_test`，不会清空或修改开发库 `expense_tracker`：

- `tests/conftest.py` 在导入应用前把 `DB_NAME`、`DB_USER`、`DB_PASSWORD` 覆盖为测试库和测试账号。
- 测试账号只需要测试库 `records` 表的 `SELECT`、`INSERT`、`DELETE` 权限，不需要 DDL。
- 测试库和 `records` 表必须由管理员预先创建；测试代码不会执行建库建表。
- 每个用例前后只清理测试库中的记录，并先校验 `SELECT DATABASE()`，拒绝操作非测试库。
- 当前共 31 个用例，覆盖添加、列表、删除、统计、金额边界、非法分类、日期、备注长度、空列表、六分类补零、重复删除和 SQL 特殊字符。

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| `/api/health` 返回 `not_configured` | `.env` 中 `DB_NAME` 或 `DB_USER` 为空；检查项目根目录的 `.env` |
| `database` 为 `mysql_unavailable` | MySQL 未启动或端口不对；检查服务状态和 `DB_HOST`/`DB_PORT` |
| `database` 为 `auth_failed` | 账号或密码错误，或账号无目标库权限 |
| `database` 为 `database_missing` | 库不存在；按上面的步骤执行 `sql/init.sql` |
| `database` 为 `timeout` | 连接超时；检查 MySQL 是否可访问，默认超时 5 秒 |
| `ModuleNotFoundError: No module named 'fastapi'` | 没有使用项目虚拟环境，或依赖未安装 |
| `[Errno 10048]` / 端口被占用 | 8000 端口已被占用；先停止旧服务或换端口 |
| 提交后返回 422 | 检查金额是否大于 0、是否最多两位小数，分类是否在六类中，日期是否合法，备注是否超过 255 字 |
| 删除返回 404 | 记录不存在或已被删除 |
| 页面中文乱码 | 确认数据库/表字符集为 `utf8mb4`，终端使用 UTF-8；数据本身通常未损坏 |
| 服务返回 500 | 查看 uvicorn 控制台日志；接口响应故意不暴露 SQL 或堆栈 |

## 安全说明

- 所有业务 SQL 使用 PyMySQL `%s` 占位符，禁止字符串拼接生成 SQL。
- 业务代码不使用 `SELECT *`，不使用无 `WHERE` 的 `DELETE`/`UPDATE`。
- 前端渲染用户内容使用 `textContent`/DOM 文本节点，不使用 `innerHTML`。
- 错误响应不返回堆栈、SQL 原文、连接串或配置值。
- `.env` 不提交；`.env.example` 只放占位符。
- 前后端同源运行，不启用 CORS，不监听公网地址。
- 应用使用专用最小权限账号 `expense_app`，测试使用 `expense_test`；两者均无 `UPDATE`、DDL、`GRANT OPTION` 或账号管理权限。
- 管理员账号仅用于初始化和管理，不应写入 `.env` 或用于日常运行。

## 第一版不包含

登录注册与多用户、收入/转账/账户余额、编辑账目、分页与复杂筛选、自定义分类、预算管理、数据导入导出、云部署。
