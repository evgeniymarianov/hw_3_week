from enum import StrEnum


class DeliveryStatus(StrEnum):
    CREATED = "created"
    COURIER_SEARCHING = "courier_searching"
    COURIER_FOUND = "courier_found"
    COURIER_ARRIVED_TO_DARKSTORE = "courier_arrived_to_darkstore"
    COURIER_ASSIGNED = "courier_assigned"
    DELIVERING = "delivering"
    PICKED_UP = "picked_up"
    COMPLETED = "completed"
