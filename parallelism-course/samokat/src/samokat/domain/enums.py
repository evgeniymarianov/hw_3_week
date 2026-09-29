from enum import StrEnum


class OrderStatus(StrEnum):
    PAID = "paid"
    COMPLETED = "completed"


class DeliveryStatus(StrEnum):
    COURIER_SEARCHING = "courier_searching"
    COURIER_FOUND = "courier_found"
    COURIER_ARRIVED_TO_DARKSTORE = "courier_arrived_to_darkstore"
    DELIVERING = "delivering"
    COMPLETED = "completed"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
