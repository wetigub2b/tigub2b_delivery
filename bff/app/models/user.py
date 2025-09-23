from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    user_name: Mapped[str] = mapped_column(String(64), unique=True)
    nick_name: Mapped[str] = mapped_column(String(30))
    phonenumber: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(1), default="0")
    del_flag: Mapped[str] = mapped_column(String(1), default="0")

    @property
    def is_active(self) -> bool:
        return self.status == "0" and self.del_flag == "0"
