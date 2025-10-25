from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, String, Text, Boolean, Enum
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "sys_user"

    # Match the actual database schema
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    dept_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    user_name: Mapped[str] = mapped_column(String(100))
    nick_name: Mapped[str] = mapped_column(String(500))
    user_type: Mapped[str | None] = mapped_column(String(2), nullable=True)
    email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phonenumber: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(1), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(1))
    del_flag: Mapped[str] = mapped_column(String(1))
    auth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    login_ip: Mapped[str | None] = mapped_column(String(128), nullable=True)
    login_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    create_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    invite_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    inviter_user_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True)

    @property
    def is_active(self) -> bool:
        return self.status == "0" and self.del_flag == "0"

    @property
    def is_admin(self) -> bool:
        # For compatibility, treat 'admin' username as admin
        return self.user_name == "admin"

    @property
    def is_super_admin(self) -> bool:
        # For compatibility, treat 'admin' username as super_admin
        return self.user_name == "admin"

    @property
    def effective_role(self) -> str:
        """Get the effective role, with fallback for compatibility"""
        # Assign role based on username for compatibility
        return "super_admin" if self.user_name == "admin" else "driver"

    @property
    def role(self) -> str:
        """Alias for effective_role for schema compatibility"""
        return self.effective_role

    @property
    def vehicle_type(self) -> str | None:
        """Placeholder for schema compatibility - field doesn't exist in sys_user"""
        return None

    @property
    def license_plate(self) -> str | None:
        """Placeholder for schema compatibility - field doesn't exist in sys_user"""
        return None

    @property
    def notes(self) -> str | None:
        """Map remark field to notes for schema compatibility"""
        return self.remark

    @property
    def created_at(self) -> datetime | None:
        """Map create_time to created_at for schema compatibility"""
        return self.create_time

    @property
    def last_login(self) -> datetime | None:
        """Map login_date to last_login for schema compatibility"""
        return self.login_date
