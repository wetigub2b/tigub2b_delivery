#!/usr/bin/env python3
"""
Script to set up the admin system for the Tigu B2B delivery system.
This script will:
1. Add missing columns to the sys_user table if they don't exist
2. Create a default admin user
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

async def check_and_add_columns():
    """Check if required columns exist and add them if missing"""

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    columns_to_add = [
        ("role", "VARCHAR(20) DEFAULT 'driver'"),
        ("email", "VARCHAR(100) NULL"),
        ("vehicle_type", "VARCHAR(50) NULL"),
        ("license_plate", "VARCHAR(20) NULL"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("last_login", "DATETIME NULL"),
        ("notes", "TEXT NULL")
    ]

    async with async_session() as session:
        try:
            # Check which columns exist
            result = await session.execute(text("DESCRIBE sys_user"))
            existing_columns = {row[0] for row in result.fetchall()}

            print(f"Existing columns: {existing_columns}")

            # Add missing columns
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    await session.execute(text(f"ALTER TABLE sys_user ADD COLUMN {column_name} {column_def}"))
                    await session.commit()
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"Column {column_name} already exists")

        except Exception as e:
            print(f"❌ Error updating database schema: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

async def create_admin_user():
    """Create a default admin user"""

    # Default admin credentials
    admin_username = "admin"
    admin_password = "admin123"  # Change this to a secure password
    admin_email = "admin@tigub2b.com"

    print("Creating admin user...")
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"Email: {admin_email}")
    print(f"Role: super_admin")

    # Create database engine
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if admin user already exists
            existing_admin = await session.execute(
                text("SELECT * FROM sys_user WHERE user_name = :username"),
                {"username": admin_username}
            )

            if existing_admin.fetchone():
                print(f"❌ Admin user '{admin_username}' already exists!")
                return

            # Hash the password
            hashed_password = get_password_hash(admin_password)

            # Create admin user with INSERT statement
            await session.execute(text("""
                INSERT INTO sys_user
                (user_name, nick_name, email, password, role, status, del_flag, created_at)
                VALUES
                (:user_name, :nick_name, :email, :password, :role, :status, :del_flag, :created_at)
            """), {
                "user_name": admin_username,
                "nick_name": "System Administrator",
                "email": admin_email,
                "password": hashed_password,
                "role": "super_admin",
                "status": "0",  # Active
                "del_flag": "0",  # Not deleted
                "created_at": datetime.now()
            })

            await session.commit()

            print("✅ Admin user created successfully!")
            print("\nYou can now login to the admin portal at:")
            print("URL: http://localhost:5173/admin/login")
            print(f"Username: {admin_username}")
            print(f"Password: {admin_password}")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

async def main():
    """Main setup function"""
    print("=== Tigu B2B Admin Setup ===")
    print()

    try:
        print("Step 1: Updating database schema...")
        await check_and_add_columns()
        print()

        print("Step 2: Creating admin user...")
        await create_admin_user()
        print()

        print("✅ Setup completed successfully!")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())