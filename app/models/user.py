import enum
from sqlalchemy import Enum as SQLEnum, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.CUSTOMER,
        nullable=False,
    )