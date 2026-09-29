from samokat.application.dto import AddressSuggestionData, UserAddressData
from samokat.infrastructure.api_connectors.external.addresses import AddressConnector
from samokat.infrastructure.api_connectors.internal.darkstore import DarkstoreConnector
from samokat.infrastructure.postgres.manager import DatabaseManager


class AddressService:
    def __init__(
        self,
        db: DatabaseManager,
        address_connector: AddressConnector,
        darkstore_connector: DarkstoreConnector,
    ) -> None:
        self.db = db
        self.address_connector = address_connector
        self.darkstore_connector = darkstore_connector

    async def suggest_addresses(
        self,
        query: str,
    ) -> list[AddressSuggestionData]:
        address_suggestions = await self.address_connector.suggest_addresses(query)
        return [
            AddressSuggestionData(
                id=suggestion.id,
                address_text=suggestion.address_text,
                lat=suggestion.lat,
                lon=suggestion.lon,
            )
            for suggestion in address_suggestions
        ]

    async def create_user_address(
        self,
        user_id: int,
        selected_address_id: str,
    ):
        address_info = await self.address_connector.get_address_full_info(
            selected_address_id,
        )
        suitable_darkstore_id = await self.darkstore_connector.get_suitable_darkstore(
            lat=address_info.lat,
            lon=address_info.lon,
        )
        await self.db.user_addresses.deactivate_user_addresses(user_id)
        await self.db.user_addresses.add_address(
            user_id=user_id,
            address_text=address_info.address_text,
            lat=address_info.lat,
            lon=address_info.lon,
            darkstore_id=suitable_darkstore_id,
        )
        await self.db.commit()

    async def select_user_address(
        self,
        user_id: int,
        address_id: int,
    ) -> None:
        await self.db.user_addresses.deactivate_user_addresses(user_id)
        await self.db.user_addresses.activate_user_address(
            user_id=user_id,
            address_id=address_id,
        )
        await self.db.commit()

    async def get_active_user_address(
        self,
        user_id: int,
    ) -> UserAddressData | None:
        return await self.db.user_addresses.get_active_user_address(
            user_id=user_id,
        )
