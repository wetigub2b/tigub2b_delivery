from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

_engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if settings.is_sqlite:
    # Ensure sqlite data directory exists (e.g. sqlite+aiosqlite:///./data/delivery.db)
    url_path = settings.database_url.split(":///", 1)[-1].split("?", 1)[0]
    if url_path != ":memory:":
        Path(url_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    _engine_kwargs = {"echo": False, "connect_args": {"check_same_thread": False}}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
