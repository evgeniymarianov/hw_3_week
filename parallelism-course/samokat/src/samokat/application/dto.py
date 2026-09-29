from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserAuthData(BaseModel):
    user_id: int | None
    hashed_password: str | None


class User(BaseModel):
    id: int
    username: str


class TokenPairData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(frozen=True)


class CartItemDetailsData(BaseModel):
    product_id: int
    title: str
    price: int
    quantity: int
    total_price: int

    model_config = ConfigDict(frozen=True)


class CartData(BaseModel):
    items: list[CartItemDetailsData]
    products_price: int

    model_config = ConfigDict(frozen=True)


class PreorderCartItemData(BaseModel):
    product_id: int
    quantity: int
    darkstore_product_id: str
    title: str
    price: int

    model_config = ConfigDict(frozen=True)


class ProductData(BaseModel):
    id: int
    category_id: int
    title: str
    price: int
    is_active: bool

    model_config = ConfigDict(frozen=True)


class ProductCardData(BaseModel):
    id: int
    category_id: int
    title: str
    description: str | None = None
    price: int
    is_active: bool

    model_config = ConfigDict(frozen=True)


class CategoryData(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(frozen=True)


class AddressSuggestionData(BaseModel):
    id: str
    address_text: str
    lat: float
    lon: float

    model_config = ConfigDict(frozen=True)


class UserAddressData(BaseModel):
    id: int
    user_id: int
    address_text: str
    darkstore_id: str
    lat: float
    lon: float
    is_active: bool

    model_config = ConfigDict(frozen=True)


class OrderItemCreateData(BaseModel):
    product_id: int
    product_title: str
    price: int
    quantity: int

    model_config = ConfigDict(frozen=True)


class OrderItemData(BaseModel):
    product_id: int
    product_title: str
    price: int
    quantity: int
    total_price: int

    model_config = ConfigDict(frozen=True)


class OrderPreviewData(BaseModel):
    items: list[OrderItemData]
    products_price: int
    delivery_price: int
    total_price: int
    darkstore_reservation_id: str

    model_config = ConfigDict(frozen=True)


class OrderCreateData(BaseModel):
    order_id: int
    status: str
    total_price: int
    delivery_id: str

    model_config = ConfigDict(frozen=True)


class OrderDeliveryData(BaseModel):
    delivery_id: str
    status: str
    estimated_delivery_at: str | None

    model_config = ConfigDict(frozen=True)


class OrderData(BaseModel):
    id: int
    status: str
    address_text: str
    total_price: int
    delivery_id: str | None

    model_config = ConfigDict(frozen=True)


class OrderDetailsData(OrderData):
    items: list[OrderItemData]
    delivery: OrderDeliveryData | None = None


class OrderReportRowData(BaseModel):
    order_id: int
    status: str
    address_text: str
    total_price: int
    created_at: datetime
    product_title: str
    price: int
    quantity: int
    item_total_price: int

    model_config = ConfigDict(frozen=True)


class ReportCreateData(BaseModel):
    report_id: str
    status: str

    model_config = ConfigDict(frozen=True)


class ReportData(BaseModel):
    id: str
    user_id: int
    status: str
    file_path: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(frozen=True)
