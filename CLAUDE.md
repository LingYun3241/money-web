# CLAUDE.md

本文件是 Claude Code 在本项目工作的项目级指南。文档中的技术栈、目录、规范与流程对后续所有改动生效。

## 0. 状态图例

| 标记 | 含义 |
|---|---|
| 【已存在】 | 当前目录中实际存在的文件或事实 |
| 【待实现】 | 规划中的文件或功能，当前**不存在** |
| 【待确认】 | 无可靠依据的参数或契约，未确认前**不得臆造**，需向用户确认 |

> 当前第一版已无【待实现】/【待确认】项；保留图例供后续变更使用。

> 本文档已按当前实现更新。第一版四项功能（添加、列表、删除、分类统计）已完成，`app/`、`static/`、`sql/`、`tests/`、`README.md` 均已存在。数据库表结构以 `sql/init.sql` 为准。

## 1. 项目状态与仓库边界

- 项目根目录：`D:\develop\AI_Coding\money web`
- git 仓库根是**父目录** `D:\develop\AI_Coding`，本项目子目录整体未跟踪；不要主动 `git commit` / `git push`。
- 项目使用 **CPython 3.12.15**，虚拟环境为项目根目录 `.venv`；本机默认的 Python 3.14 不用于本项目。
- MySQL 服务端为 **5.7.43**，服务 `MySQL57` 已运行并在本机 `3306` 端口监听。`mysql` 客户端不在 PATH 中，实际路径为 `C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe`。
- `.env` 已配置并被 `.gitignore` 忽略；`.env.example` 为占位符模板。不要读取、打印或提交 `.env`。
- 现有 `.gitignore` 已覆盖：`.env`、`.venv/`、`__pycache__/`、`*.pyc`、`.pytest_cache/`。`.claude/settings.local.json` 不在 `.gitignore` 中，不要修改该文件。

## 2. 项目概况

本地运行的个人支出记账 Web 项目，单用户、单机，第一版最小闭环已完成。

### 2.1 核心功能（第一版，已完成）

1. 添加账目
2. 查看账目列表
3. 删除账目
4. 分类统计

以上四项均已实现，前端通过 Fetch 调用同源 `/api/...` 接口。

### 2.2 固定分类

共六个，不允许自定义、不允许扩展：

| 分类 | 分类 | 分类 |
|---|---|---|
| 餐饮 | 交通 | 购物 |
| 娱乐 | 居住 | 其它 |

- 后端校验是分类白名单的**唯一权威**；前端下拉框可静态写死这六项，但必须与后端完全一致。
- 非法分类必须被后端拒绝（422），不能静默归入「其它」。

### 2.3 第一版明确不做

- 登录注册、多用户、鉴权
- 收入、转账、账户余额
- 编辑账目
- 分页和复杂筛选
- 自定义分类
- 预算管理
- 数据导入导出
- 云部署、微服务

不得以「顺手」「以后要用」为理由提前实现上述功能或为其搭抽象层。

## 3. 技术栈（硬约束）

### 3.1 选型

| 类别 | 内容 |
|---|---|
| 必须使用 | Python、FastAPI、PyMySQL（同步驱动）、原生 HTML、原生 CSS、原生 JavaScript、Fetch API、本地 MySQL |
| 允许使用 | Uvicorn、Pydantic、python-dotenv、pytest、httpx |
| 禁止使用 | Vue、React、TypeScript、SQLAlchemy 或任何 ORM、异步 MySQL 驱动、Node/npm 构建流程、Docker、云服务、消息队列 |

`requirements.txt` 已固定 `fastapi`、`uvicorn[standard]`、`pymysql`、`python-dotenv`、`pytest`、`httpx` 这 6 个直接依赖的版本（`==`）；间接依赖未完全锁定，重建环境仍可能存在版本差异。新增依赖前必须说明包名、用途、版本、来源并等待用户确认。

### 3.2 实现硬约束

- 所有访问数据库的 FastAPI 端点一律用普通 `def`，由 FastAPI 在线程池中执行。
- **禁止**在 `async def` 中执行阻塞的数据库查询；本项目默认不需要 `async def` 端点。
- PyMySQL 使用同步连接，不使用 `aiomysql` 等异步驱动。
- 前后端优先同源运行：由 FastAPI 提供 `static/` 下的前端资源，前端用相对路径请求 `/api/...`。
- 不引入 CORS、不另起前端开发服务器（除非用户明确要求）。
- 不为简单功能引入不必要的框架、缓存层、消息机制或抽象层。

## 4. 目录约定

### 4.1 当前结构

以下文件均已存在；`.env` 为本地配置，已被 `.gitignore` 忽略，不得读取或提交。

```text
项目根目录/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  └─ routers/
│     ├─ __init__.py
│     └─ records.py
├─ static/
│  ├─ index.html
│  ├─ style.css
│  └─ app.js
├─ sql/
│  └─ init.sql
├─ tests/
│  ├─ conftest.py
│  └─ test_records_api.py
├─ .env                       # 本地配置，已忽略，不读取
├─ .env.example               # 占位符模板
├─ .gitignore
├─ requirements.txt
├─ README.md
└─ CLAUDE.md
```

新增文件应遵循此结构，偏离前先说明理由。

### 4.2 文件职责与边界

| 位置 | 职责 | 禁止 |
|---|---|---|
| `app/main.py` | 创建 FastAPI 实例、挂载静态目录、注册路由、根页面与健康检查 | 不写业务 SQL、不放业务校验 |
| `app/config.py` | 从环境变量/`.env` 读取数据库连接配置 | 不硬编码任何凭据；不打印配置值 |
| `app/db.py` | 连接获取、游标、事务、数据库健康检查 | 不写 HTTP 逻辑 |
| `app/models.py` | 分类 `Literal` 与常量等纯数据定义 | 不放 ORM 模型（本项目无 ORM） |
| `app/schemas.py` | Pydantic 请求/响应模型、字段与分类校验 | 不放 SQL |
| `app/routers/records.py` | HTTP 参数、状态码、通过 `get_cursor` 执行参数化 SQL、组装响应 | 不拼接 SQL、不自行创建连接 |
| `static/` | 原生前端页面、样式、脚本 | 不使用框架、无构建步骤、无 npm 依赖 |
| `sql/init.sql` | 幂等建库建表 | 不含 `DROP` / `TRUNCATE` / `DELETE` / `ALTER` |
| `tests/` | pytest 测试，使用独立测试库和专用测试账号 | 不依赖真实生产数据；不修改开发库；不执行建库建表 |

## 5. 开发规范

### 5.1 命名与注释

- 模块、函数、变量：`snake_case`；类：`PascalCase`；常量：`UPPER_SNAKE_CASE`。
- 注释和文档用中文，标识符用英文；不写与代码重复的废话注释。
- 修改前先读相邻代码，保持同一文件内的风格一致。

### 5.2 数据与校验

- **金额**：MySQL 用 `DECIMAL(10,2)`；Python 用 `Decimal`；**禁止 `float` 参与金额计算或持久化**。JSON 中金额为字符串（如 `"12.50"`），前后端保持一致。
- **日期**：记账日期用 `DATE`，请求格式为 `YYYY-MM-DD`；前端默认填入浏览器本地当天日期，后端按 `DATE` 原样存储和返回，未做额外时区换算。
- **校验**：金额必须大于 0、最多两位小数；分类必须命中六分类；日期必填且合法；备注可为空，最长 255 个字符。非法输入返回 422，由 Pydantic 承担。
- **删除**：按主键单条删除；成功返回 204；不存在返回 404；以影响行数是否为 0 判定。
- **列表**：第一版不分页，固定按 `record_date DESC, id DESC` 返回。
- **统计**：固定返回六个分类；返回总金额、总笔数以及各分类金额，没有账目的分类补 `"0.00"`。

### 5.3 API 与错误

实际接口如下，OpenAPI 文档可在 `/docs` 查看：

| 方法 | 路径 | 用途 | 成功状态码 |
|---|---|---|---|
| GET | `/api/health` | 健康检查，包含数据库状态 | 200 |
| POST | `/api/records` | 添加账目 | 201 |
| GET | `/api/records` | 账目列表 | 200 |
| DELETE | `/api/records/{record_id}` | 删除账目 | 204 |
| GET | `/api/statistics` | 分类统计 | 200 |

- 统一使用 JSON；成功返回 2xx，非法输入 422，资源不存在 404。
- 错误用 `HTTPException`，响应中不得暴露堆栈、SQL 原文、连接串或配置值。
- 不额外包装统一响应体（如 `{code, data, msg}`），除非用户明确要求。

### 5.4 前端

- 原生 HTML/CSS/JavaScript，无构建步骤、无 npm 依赖。
- 请求统一用 Fetch API，路径为同源相对路径。
- 渲染用户输入（备注等）使用 `textContent` 或等价安全 API，**禁止用 `innerHTML` 拼接未转义数据**。
- 前端只做展示与交互，业务校验以后端为准；前端校验不能替代后端校验。

### 5.5 依赖与复杂度

- 新增依赖前必须说明包名、用途、版本、来源并等待用户确认。
- 不升级、不降级已有依赖，不批量格式化无关文件。
- 不提前抽象 repository/service 层；`db.py` 与路由足以支撑第一版。

## 6. 数据库安全规则（硬规则）

以下规则不允许以「方便调试」「临时一下」为由绕过：

1. **凭据来源**：数据库主机、端口、库名、账号、密码只从环境变量/`.env` 读取；`.env` 已被 `.gitignore` 忽略。密码、Token、连接串等敏感凭据禁止出现在源码、文档、测试、日志、提交信息、命令行参数中；文档可以记录库名和账号名，但不得包含密码。
2. **不读密**：不读取、不打印、不回显 `.env` 内容；命令示例只用占位符；不使用 `-p<密码>` 这种明文形式。
3. **字符集**：连接统一使用 `utf8mb4`。
4. **最小权限**：应用账号 `expense_app` 仅对 `expense_tracker.records` 具有 `SELECT`、`INSERT`、`DELETE`；测试账号 `expense_test` 仅对 `expense_tracker_test.records` 具有 `SELECT`、`INSERT`、`DELETE`。两者均不授予 `UPDATE`、DDL、`GRANT OPTION` 或账号管理权限；`USAGE ON *.*` 仅为登录所需，不授予数据权限。管理员账号仅用于初始化和管理。
5. **初始化脚本**：`sql/init.sql` 只允许幂等写法（`CREATE DATABASE IF NOT EXISTS`、`CREATE TABLE IF NOT EXISTS`）；禁止包含 `DROP`、`TRUNCATE`、`DELETE`、`ALTER`。执行前必须由用户确认。
6. **参数化查询**：所有 SQL 使用 PyMySQL 的 `%s` 占位符传参；**禁止 f-string、`%` 字符串格式化、`+`、`.format()` 或任何字符串拼接生成 SQL**；表名、列名只能是代码中的字面量，不能来自用户输入。
7. **事务**：写操作使用事务，成功 `commit()`，异常 `rollback()`；连接和游标必须在 `finally` 或 contextmanager 中关闭。
8. **写操作范围**：禁止无 `WHERE` 的 `DELETE` / `UPDATE`；业务代码禁止 `SELECT *`，只查询需要的列。
9. **连接范围**：只连接本地 MySQL；禁止连接外部/远程数据库，除非用户明确要求。
10. **破坏性命令**：未经用户明确要求并二次确认，禁止执行 `DROP DATABASE`、`DROP TABLE`、`TRUNCATE`、`ALTER`、`CREATE USER`、`GRANT` 等命令。
11. **示例文件**：`.env.example` 只写占位符（如 `DB_PASSWORD=your_password_here`、`TEST_DB_PASSWORD=your_test_password_here`），不得包含真实值。
12. **配置参数**：数据库主机、端口、库名、账号、密码已配置在 `.env` 中；本文档和代码不记录密码、Token 或连接串。表结构以 `sql/init.sql` 为准。
13. **结构变更**：不使用迁移工具；表结构变更 = 修改 `sql/init.sql` 并说明影响，经用户确认后执行。
14. **验证取数**：核对数据只用只读 `SELECT` / `COUNT`；禁止为验证而修改或清空数据。

## 7. 验证流程

按「环境 → 启动 → 自动化测试 → 手工验收 → 数据核对」执行。首次安装依赖、创建数据库、启动服务前均须用户确认。

### 7.1 环境准备

项目已创建 `.venv`（CPython 3.12.15）并安装依赖。需要重建时：

```bash
# 在项目根目录
py -V:Astral/CPython3.12.15 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

- Windows Git Bash 使用 `./.venv/Scripts/python.exe`；PowerShell 使用 `.\.venv\Scripts\python.exe`。
- `requirements.txt` 已固定 6 个直接依赖版本；间接依赖未完全锁定，重建环境仍可能存在差异。新增依赖须先确认。

### 7.2 启动

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- 只绑定 `127.0.0.1`，不监听 `0.0.0.0`。
- 浏览器访问 `http://127.0.0.1:8000/` 应直接打开前端页面（同源）。

### 7.3 自动化测试

```bash
./.venv/Scripts/python.exe -m pytest -q
```

- 测试框架使用 pytest，接口测试使用 FastAPI `TestClient`。
- 测试使用独立测试库 `expense_tracker_test` 和专用测试账号 `expense_test`；测试库/表由管理员预先创建，测试代码不执行建库建表。
- `tests/conftest.py` 在导入应用前覆盖 `DB_NAME`、`DB_USER`、`DB_PASSWORD`，确保被测应用只连接测试库。
- 测试只清理测试库中的记录，不修改开发库；不得输出 `.env` 中的敏感值。
- 当前共 31 个用例；提交结果前必须实际运行，测试失败要原样给出输出，不得只写「已修复」。

### 7.4 手工验收清单

1. 添加一条餐饮支出 → 列表可见，金额、分类、日期、备注正确。
2. 添加六种分类各一条 → 分类统计金额与总笔数正确。
3. 非法分类提交 → 后端返回 422，数据库无新增行。
4. 金额为 0 或负数 → 返回 422。
5. 删除某条 → 列表不再出现，数据库对应行消失。
6. 删除不存在的 ID → 返回 404。
7. 刷新页面 → 数据从后端重新加载，不依赖浏览器内存。

### 7.5 通过标准

- pytest 退出码为 0；
- 每个接口的状态码与关键响应字段可观察；
- 数据库行数/data 变化可观察（只读查询核对）；
- 「服务没崩」不算通过；未执行的步骤必须明确说明未执行。

## 8. 协作流程

1. **一次只做一件事**：完成用户当前要求的最小闭环，不做未被要求的重构、优化或功能。
2. **先读后改**：修改前先读相关文件与相邻实现，保持风格一致。
3. **模糊先问**：需求不明确或涉及需要用户确认的参数时，先给简短方案与推荐，再等待确认。
4. **小步聚焦**：改动范围只覆盖任务本身；发现相邻问题可以指出，但不顺手修改。
5. **禁止事项（未经明确要求）**：`git commit` / `git push`、删除文件、修改 `.env`、安装依赖、创建数据库/表/账号、启动或停止服务。
6. **破坏性操作先确认**：删库删表、覆盖数据、删除文件、重置环境前必须说明后果并等待确认。
7. **如实报告**：测试失败给输出；跳过的步骤说明原因；计划中的内容不得说成已完成。
8. **配置边界**：不创建或修改 settings 文件、全局配置、`.claude/settings.local.json`。
9. **提交信息**：如用户要求提交，使用中文提交说明，风格与仓库现状一致；不擅自推送。

## 9. 已知限制与后续事项

以下为当前实现的已知限制，不是未确认的接口契约：

| 项目 | 当前状态 |
|---|---|
| 依赖版本 | `requirements.txt` 已固定 6 个直接依赖版本；间接依赖未完全锁定，重建环境仍可能有差异 |
| 测试客户端 | Starlette 提示 `httpx` 用于 `TestClient` 已弃用，建议 `httpx2`，当前未处理 |
| 日期时区 | 前端使用浏览器本地日期，后端按 `DATE` 存储，未做额外时区换算 |
| MySQL 版本 | 5.7.43 已停止官方维护，升级需另行评估 |
| 账号权限 | 应用/测试账号已最小权限；管理员账号仍保留管理权限，仅用于初始化和管理 |
| 自动化范围 | 已有 31 个 pytest 用例；未配置 CI，也未固化浏览器端到端测试 |

## 10. 执行前自检

每次开始任务前快速核对：

- [ ] 是否只读了当前任务需要的文件？
- [ ] 是否涉及需要用户确认的破坏性操作？
- [ ] 是否读取或输出了 `.env` / 密码 / Token？
- [ ] 是否执行了破坏性命令、安装依赖、启动服务或 commit？
- [ ] 改动是否足够小，是否遵守了普通 `def` + 同步 PyMySQL + 参数化 SQL？
- [ ] 测试是否只使用独立测试库，未修改开发库？
- [ ] 是否保持应用账号仅有 `SELECT`、`INSERT`、`DELETE`，未引入 `UPDATE` / DDL / `GRANT`？
- [ ] 是否实际运行验证，并如实报告结果？
