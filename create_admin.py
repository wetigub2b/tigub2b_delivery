#!/usr/bin/env python3
"""
Script to create a default admin user for the Tigu B2B delivery system.
Run this script to create an admin user that can access the admin portal.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the BFF directory to Python path
sys.path.append('./bff')

from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

# Database configuration - update these values to match your setup
DATABASE_URL = "mysql+aiomysql://tigu:T1gu125443!@127.0.0.1:3306/tigu_b2b"

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
                select(User).where(User.user_name == admin_username)
            )

            if existing_admin.fetchone():
                print(f"❌ Admin user '{admin_username}' already exists!")
                return

            # Hash the password
            hashed_password = get_password_hash(admin_password)

            # Create admin user
            admin_user = User(
                user_name=admin_username,
                nick_name="System Administrator",
                email=admin_email,
                password=hashed_password,
                role="super_admin",
                status="0",  # Active
                del_flag="0",  # Not deleted
                created_at=datetime.now()
            )

            session.add(admin_user)
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
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("=== Tigu B2B Admin User Creator ===")
    print()

    # Update the DATABASE_URL above before running
    print("📝 Before running this script:")
    print("1. Update the DATABASE_URL in this script with your database credentials")
    print("2. Make sure your database is running and accessible")
    print("3. Ensure the database tables are created (run migrations)")
    print()

    response = input("Have you updated the DATABASE_URL? (y/n): ")
    if response.lower() != 'y':
        print("Please update the DATABASE_URL first and run again.")
        sys.exit(1)

    asyncio.run(create_admin_user())