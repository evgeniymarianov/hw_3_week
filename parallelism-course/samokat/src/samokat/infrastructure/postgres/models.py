from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, String, text


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user_address_id: Mapped[int] = mapped_column(
        ForeignKey("user_addresses.id"),
    )

    status: Mapped[str] = mapped_column(
        index=True,
    )

    address_text: Mapped[str]

    darkstore_id: Mapped[str] = mapped_column(
        index=True,
    )

    darkstore_reservation_id: Mapped[str]

    delivery_id: Mapped[str | None]

    total_price: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(
        String(128),
    )


class UserAddressModel(Base):
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    address_text: Mapped[str]

    darkstore_id: Mapped[str] = mapped_column(index=True)

    lat: Mapped[float]
    lon: Mapped[float]

    is_active: Mapped[bool]


class CartItemModel(Base):
    __tablename__ = "cart_items"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        primary_key=True,
    )
    quantity: Mapped[int]


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_title: Mapped[str]
    price: Mapped[int] = mapped_column()
    quantity: Mapped[int] = mapped_column()


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    darkstore_product_id: Mapped[str] = mapped_column(
        unique=True,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        index=True,
    )
    title: Mapped[str]
    description: Mapped[str | None]
    price: Mapped[int]
    is_active: Mapped[bool] = mapped_column(
        index=True,
    )


class DarkstoreProductModel(Base):
    __tablename__ = "darkstore_products"

    darkstore_id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        primary_key=True,
    )
    is_available: Mapped[bool] = mapped_column(
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(index=True)
    file_path: Mapped[str | None]
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
