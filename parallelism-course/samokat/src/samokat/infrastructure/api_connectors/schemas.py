from pydantic import BaseModel, ConfigDict


class ResolvedAddressData(BaseModel):
    address_text: str
    lat: float
    lon: float

    model_config = ConfigDict(frozen=True)


class AddressSuggestionData(BaseModel):
    id: str
    address_text: str
    lat: float
    lon: float

    model_config = ConfigDict(frozen=True)


class DeliveryData(BaseModel):
    delivery_id: str
    order_id: int
    status: str

    model_config = ConfigDict(frozen=True)


class DeliveryInfoData(BaseModel):
    delivery_id: str
    status: str
    estimated_delivery_at: str | None

    model_config = ConfigDict(frozen=True)


class DarkstoreProductData(BaseModel):
    sku_id: str
    title: str
    description: str | None
    category_id: int
    category_title: str
    price: int
    is_active: bool
    quantity: int | None = None
    is_available: bool = True

    model_config = ConfigDict(frozen=True)


class DarkstoreReservationData(BaseModel):
    reservation_id: str

    model_config = ConfigDict(frozen=True)


class DarkstoreReservationItemData(BaseModel):
    sku_id: str
    quantity: int

    model_config = ConfigDict(frozen=True)
