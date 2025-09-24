#!/usr/bin/env python3
"""
Debug script to test admin authentication
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

# Add the BFF directory to Python path
sys.path.append('./bff')

from app.models.user import User
from app.core.security import verify_password

# Database configuration
DATABASE_URL = "mysql+aiomysql://tigu:T1gu125443!@127.0.0.1:3306/tigu_b2b"

async def debug_admin_login():
    """Debug the admin login process"""

    username = "admin"
    password = "admin123"

    print("=== Debug Admin Login ===")
    print(f"Testing login for: {username}")

    # Create database engine
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("\n1. Testing basic query...")
            # First, let's see what columns actually exist
            result = await session.execute(text("DESCRIBE sys_user"))
            columns = result.fetchall()
            print("Available columns:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")

            print("\n2. Testing user lookup...")
            # Try to find the admin user using basic query
            result = await session.execute(
                text("SELECT user_id, user_name, nick_name, password, status, del_flag FROM sys_user WHERE user_name = :username"),
                {"username": username}
            )
            user_row = result.fetchone()

            if not user_row:
                print(f"❌ User '{username}' not found!")
                return

            print(f"✅ User found: {user_row[1]} (ID: {user_row[0]})")
            print(f"   Status: {user_row[4]}, Del_flag: {user_row[5]}")

            print("\n3. Testing password verification...")
            stored_password = user_row[3]
            if verify_password(password, stored_password):
                print("✅ Password verification successful")
            else:
                print("❌ Password verification failed")

            print("\n4. Testing SQLAlchemy model...")
            try:
                # Try using the User model
                result = await session.execute(select(User).where(User.user_name == username))
                user = result.scalars().first()

                if user:
                    print(f"✅ SQLAlchemy model works")
                    print(f"   User ID: {user.user_id}")
                    print(f"   Username: {user.user_name}")
                    print(f"   Active: {user.is_active}")
                    print(f"   Admin: {user.is_admin}")
                    print(f"   Effective role: {user.effective_role}")
                else:
                    print("❌ SQLAlchemy model returned no user")

            except Exception as e:
                print(f"❌ SQLAlchemy model error: {e}")

        except Exception as e:
            print(f"❌ Error during debug: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_admin_login())