"""Init SQLite DB for delivery BFF: create tables + seed minimal login data.

Run from bff/:  ./.venv/bin/python init_sqlite.py
DB path comes from DATABASE_URL env (sqlite+aiosqlite:///...).
"""
import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base

import app.models  # noqa: F401  (register all models)


MARKS_DDL = """
CREATE TABLE IF NOT EXISTS tigu_driver_marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    type VARCHAR(50),
    description TEXT,
    shop_id BIGINT,
    warehouse_id BIGINT,
    is_active SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SHOP_DDL = """
CREATE TABLE IF NOT EXISTS tigu_shop (
    id BIGINT PRIMARY KEY,
    name TEXT,
    shop_info VARCHAR(255)
)
"""


async def main() -> None:
    settings = get_settings()
    print(f"DB: {settings.database_url}")
    if not settings.is_sqlite:
        print("DATABASE_URL is not sqlite; aborting.")
        sys.exit(1)

    engine = create_async_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(MARKS_DDL))
        await conn.execute(text(SHOP_DDL))

    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        from app.models.driver import Driver
        from app.models.order import Warehouse
        from app.models.user import User
        from sqlalchemy import select

        admin = (await s.execute(select(User).where(User.user_name == "admin"))).scalars().first()
        if not admin:
            s.add(User(
                user_id=1, user_name="admin", nick_name="admin",
                phonenumber="15888888888", password=get_password_hash("admin123"),
                status="0", del_flag="0",
            ))
            print("seeded admin / admin123")
        driver_user = (await s.execute(select(User).where(User.phonenumber == "15666666666"))).scalars().first()
        if not driver_user:
            s.add(User(
                user_id=2, user_name="driver_15666666666", nick_name="driver",
                phonenumber="15666666666", password=get_password_hash("driver123"),
                status="0", del_flag="0",
            ))
            print("seeded driver 15666666666 / 123456")
        if not (await s.execute(select(Driver).where(Driver.phone == "15888888888"))).scalars().first():
            s.add(Driver(name="Test Driver", phone="15888888888", status=1,
                         rating=Decimal("5.00"), total_deliveries=0))
        if not (await s.execute(select(Driver).where(Driver.phone == "15666666666"))).scalars().first():
            s.add(Driver(name="driver", phone="15666666666", status=1,
                         rating=Decimal("5.00"), total_deliveries=0))
        wh = (await s.execute(select(Warehouse).where(Warehouse.code == "WH001"))).scalars().first()
        if not wh:
            s.add(Warehouse(code="WH001", name="Warehouse 1", contact_person="Admin",
                            contact_phone="0000000000", line1="940 Sheldon Ct",
                            city="Burlington", province="Ontario", country="Canada",
                            postal_code="L7L 5K6"))
            print("seeded warehouse WH001")
        n = (await s.execute(text("SELECT COUNT(*) FROM tigu_driver_marks"))).scalar()
        if not n:
            await s.execute(text(
                "INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description, warehouse_id) "
                "VALUES ('Warehouse 1 - Burlington', 43.3258, -79.7991, 'Warehouse', 'Main warehouse', 1)"
            ))
            await s.execute(text(
                "INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description, shop_id) VALUES "
                "('Vendor - Downtown Toronto', 43.6532, -79.3832, 'Vendor', 'Vendor pickup', 2001),"
                "('GreenBuild Supplies', 43.5890, -79.6441, 'Vendor', 'Mississauga', 2002),"
                "('Modern Timber Co.', 43.8561, -79.3370, 'Vendor', 'Markham', 2003)"
            ))
            print("seeded 4 marks")
        await s.commit()
    await engine.dispose()
    print("SQLite init done.")


if __name__ == "__main__":
    asyncio.run(main())
