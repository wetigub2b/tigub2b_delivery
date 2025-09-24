#!/usr/bin/env python3
"""
Script to update the admin user's password
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the BFF directory to Python path
sys.path.append('./bff')

from app.core.security import get_password_hash

# Database configuration
DATABASE_URL = "mysql+aiomysql://tigu:T1gu125443!@127.0.0.1:3306/tigu_b2b"

async def fix_admin_password():
    """Update the admin user's password"""

    username = "admin"
    new_password = "admin123"

    print("=== Fixing Admin Password ===")
    print(f"Updating password for: {username}")

    # Create database engine
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Hash the new password
            hashed_password = get_password_hash(new_password)
            print(f"New hashed password: {hashed_password[:20]}...")

            # Update the admin user's password
            result = await session.execute(
                text("UPDATE sys_user SET password = :password WHERE user_name = :username"),
                {"password": hashed_password, "username": username}
            )

            await session.commit()

            if result.rowcount > 0:
                print("✅ Admin password updated successfully!")
                print(f"Username: {username}")
                print(f"Password: {new_password}")
            else:
                print(f"❌ No user found with username '{username}'")

        except Exception as e:
            print(f"❌ Error updating password: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_admin_password())