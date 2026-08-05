# CloudPatch 后端连接阿里云 RDS MySQL

本文档说明 CloudPatch 的 Python FastAPI 后端如何连接阿里云 RDS MySQL，并给出一套适合团队协作的 SQLAlchemy 2.x 异步连接方案。

## 1. 数据库信息

| 配置项 | 值 |
| --- | --- |
| 数据库引擎 | MySQL 8.0 |
| 地域 | 华东 1（杭州） |
| RDS 实例 ID | `rm-bp1i85v63d7gl9221` |
| 公网地址 | `rm-bp1i85v63d7gl9221-public.mysql.rds.aliyuncs.com` |
| 端口 | `3306` |
| 数据库名 | `cloudpatch` |
| 普通读写账号 | `cloudpatch` |
| 密码 | 仅保存在本地环境变量或密钥管理服务中 |

> 当前 RDS 白名单包含 `0.0.0.0/0`，即允许任意公网 IP 尝试连接。开发阶段可临时使用，但建议尽快改为三位开发者的公网 IP，或通过 VPN、堡垒机等受控网络访问。

## 2. 推荐技术方案

本文使用以下组件：

- FastAPI
- SQLAlchemy 2.x 异步 ORM
- `asyncmy` 异步 MySQL 驱动
- `pydantic-settings` 环境变量配置
- Alembic 数据库迁移

推荐目录结构：

```text
app/
├── api/
│   └── health.py
├── core/
│   └── config.py
├── db/
│   ├── base.py
│   └── session.py
├── models/
│   └── user.py
└── main.py
.env
.env.example
```

## 3. 安装依赖

使用 `pip`：

```bash
pip install "fastapi" "uvicorn[standard]" "sqlalchemy[asyncio]>=2,<3" asyncmy "pydantic-settings>=2,<3" alembic
```

如果项目使用 Poetry、uv 或其他依赖管理工具，请添加相同的软件包。

## 4. 配置环境变量

在项目根目录创建 `.env`：

```env
DB_HOST=your-rds-instance.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=cloudpatch
DB_USER=cloudpatch
DB_PASSWORD=<set-in-local-env>
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
```

创建可提交到 Git 的 `.env.example`：

```env
DB_HOST=your-rds-instance.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=cloudpatch
DB_USER=cloudpatch
DB_PASSWORD=
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
```

确认 `.gitignore` 包含：

```gitignore
.env
.env.*.local
```

不要把真实密码写进源码、Dockerfile、GitHub Actions 日志或团队聊天记录。

## 5. 读取配置

创建 `app/core/config.py`：

```python
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: SecretStr
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

使用 `URL.create()` 组装连接地址，可以正确处理密码中的 `@`、`#`、`:`、`/` 等特殊字符，避免手工拼接 URL 时的编码问题。

## 6. 创建异步 Engine 和 Session

创建 `app/db/session.py`：

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

关键点：

- 整个应用共用一个 `AsyncEngine`，不要在每个请求中重复创建 Engine。
- 每个请求创建独立的 `AsyncSession`，不要在并发请求之间共享 Session。
- `pool_pre_ping=True` 会在借出连接前检测失效连接。
- `pool_recycle=1800` 会定期回收旧连接，降低长时间空闲连接被服务端断开后产生错误的概率。
- 写操作成功后应在业务代码中显式执行 `await session.commit()`；异常时依赖会回滚事务。

## 7. 声明 ORM Base 和示例模型

创建 `app/db/base.py`：

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

示例模型 `app/models/user.py`：

```python
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
```

生产项目应使用 Alembic 管理表结构，不要在每次应用启动时调用 `Base.metadata.create_all()`。

## 8. FastAPI 生命周期管理

创建 `app/main.py`：

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.health import router as health_router
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    yield

    await engine.dispose()


app = FastAPI(title="CloudPatch API", lifespan=lifespan)
app.include_router(health_router)
```

应用启动时会执行一次 `SELECT 1`。如果数据库配置错误或无法连接，应用会直接启动失败，从而尽早暴露配置问题；应用关闭时会释放连接池。

## 9. 数据库健康检查接口

创建 `app/api/health.py`：

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db")
async def database_health(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"database": "ok"}
```

启动服务：

```bash
uvicorn app.main:app --reload
```

验证：

```bash
curl http://127.0.0.1:8000/health/db
```

预期响应：

```json
{"database":"ok"}
```

## 10. 业务代码示例

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User


router = APIRouter(prefix="/users", tags=["users"])


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


@router.get("", response_model=list[UserRead])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserRead]:
    result = await session.scalars(select(User).order_by(User.id))
    return [UserRead.model_validate(user) for user in result]
```

不要使用字符串拼接构造 SQL。优先使用 SQLAlchemy 表达式；必须执行原生 SQL 时使用绑定参数：

```python
from sqlalchemy import text

result = await session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email},
)
```

## 11. Alembic 迁移

初始化异步迁移目录：

```bash
alembic init -t async migrations
```

在 `migrations/env.py` 中导入 `Base` 和所有模型，并设置：

```python
from app.db.base import Base
from app.models.user import User  # noqa: F401

target_metadata = Base.metadata
```

不要把真实数据库密码写入 `alembic.ini`。让迁移脚本从 `app.core.config.settings.database_url` 获取连接配置。

创建和执行迁移：

```bash
alembic revision --autogenerate -m "create users table"
alembic upgrade head
```

执行迁移前应人工检查自动生成的 migration 文件，尤其是删除列、删除表和类型变更。

## 12. 连接池容量规划

每个 Uvicorn worker 都有独立连接池。数据库理论最大连接占用可按下式估算：

```text
worker 数量 × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

例如使用 4 个 worker、`pool_size=5`、`max_overflow=10`，峰值可能达到 60 个连接。应确保该值低于 RDS 实例允许的最大连接数，并为 DMS、迁移任务和人工排查保留余量。

本地开发建议从以下配置开始：

```env
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=1800
```

生产环境应根据 worker 数、并发量、SQL 执行时间和 RDS 最大连接数重新计算。

## 13. 常见错误

### `Access denied for user` / MySQL 1045

检查：

- 用户名和密码是否正确。
- 账号状态是否为可用。
- `cloudpatch` 账号是否拥有 `cloudpatch` 数据库的读写权限。
- 密码中有特殊字符时是否被手工拼接的 URL 错误解析。

### `Can't connect to MySQL server` / MySQL 2003

检查：

- Host 是否使用公网地址，而不是 RDS 内网地址。
- 端口是否为 `3306`。
- 本地网络、防火墙或公司代理是否阻止 3306 端口。
- RDS 公网地址和 IP 白名单是否仍然生效。

可以先测试 TCP 端口：

```bash
nc -vz rm-bp1i85v63d7gl9221-public.mysql.rds.aliyuncs.com 3306
```

### 连接偶发失效

确认已设置：

```python
pool_pre_ping=True
pool_recycle=1800
```

同时检查 RDS 监控中的连接数、CPU、慢 SQL 和网络指标。

### 数据库连接数过多

- 不要为每次请求创建新 Engine。
- 确保 Session 使用 `async with` 或 FastAPI `yield` 依赖正确关闭。
- 检查 Uvicorn worker 数与每个 worker 的连接池配置。
- 不要跨多个异步任务共享一个 `AsyncSession`。

## 14. 团队安全约定

1. `.env` 只保存在开发者本地，不提交 Git。
2. 测试、预发布、生产环境使用不同数据库账号和密码。
3. 应用账号只授予业务数据库所需的最小权限，不使用高权限账号运行后端服务。
4. 三位开发者尽量使用独立账号，便于撤销权限和审计。
5. 尽快把 `0.0.0.0/0` 替换为团队成员的公网 IP。
6. 定期轮换数据库密码；成员离开项目时立即撤销账号或更换共享密码。
7. 开启 RDS SSL 后，在客户端配置证书校验，避免公网链路被窃听或中间人攻击。
8. 生产环境使用云端密钥管理服务注入密码，不把密码固化在镜像中。

## 15. 参考资料

- [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy MySQL asyncmy dialect](https://docs.sqlalchemy.org/en/20/dialects/mysql.html#asyncmy)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [阿里云 RDS MySQL 设置 IP 白名单](https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/configure-an-ip-address-whitelist-for-an-apsaradb-rds-for-mysql-instance)
- [阿里云 RDS MySQL 申请外网地址](https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/apply-for-or-release-a-public-endpoint-for-an-apsaradb-rds-for-mysql-instance)
