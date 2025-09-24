#!/usr/bin/env python3
"""
Script to create a basic admin user using only existing database columns.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the BFF directory to Python path
sys.path.append('./bff')

from app.core.security import get_password_hash

# Database configuration
DATABASE_URL = "mysql+aiomysql://tigu:T1gu125443!@127.0.0.1:3306/tigu_b2b"

async def create_basic_admin():
    """Create a basic admin user using only existing columns"""

    # Default admin credentials
    admin_username = "admin"
    admin_password = "admin123"
    admin_nick_name = "Administrator"

    print("=== Creating Basic Admin User ===")
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"Nick Name: {admin_nick_name}")

    # Create database engine
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                text("SELECT user_name FROM sys_user WHERE user_name = :username"),
                {"username": admin_username}
            )

            if result.fetchone():
                print(f"❌ Admin user '{admin_username}' already exists!")
                return

            # Hash the password
            hashed_password = get_password_hash(admin_password)

            # Create admin user with only basic columns
            await session.execute(text("""
                INSERT INTO sys_user (user_name, nick_name, password, status, del_flag)
                VALUES (:user_name, :nick_name, :password, :status, :del_flag)
            """), {
                "user_name": admin_username,
                "nick_name": admin_nick_name,
                "password": hashed_password,
                "status": "0",  # Active
                "del_flag": "0"  # Not deleted
            })

            await session.commit()

            print("✅ Basic admin user created successfully!")
            print("\nYou can now login at:")
            print("URL: http://localhost:5173/admin/login")
            print(f"Username: {admin_username}")
            print(f"Password: {admin_password}")
            print("\n⚠️  IMPORTANT: This user was created with basic columns only.")
            print("   The admin features may need to be updated to work with the existing schema.")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_basic_admin())