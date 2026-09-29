from datetime import UTC, datetime
from pathlib import Path

from openpyxl import Workbook

from samokat.application.dto import OrderReportRowData
from samokat.config import ReportsConfig


class OrdersReportExcelWriter:
    def __init__(self, config: ReportsConfig) -> None:
        self.config = config

    def write(self, report_id: str, rows: list[OrderReportRowData]) -> Path:
        file_path = self._get_report_path(report_id)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Orders"
        sheet.append(
            [
                "order_id",
                "status",
                "address_text",
                "total_price",
                "created_at",
                "product_title",
                "price",
                "quantity",
                "item_total_price",
            ],
        )

        for row in rows:
            sheet.append(
                [
                    row.order_id,
                    row.status,
                    row.address_text,
                    row.total_price,
                    self._prepare_datetime(row.created_at),
                    row.product_title,
                    row.price,
                    row.quantity,
                    row.item_total_price,
                ],
            )

        workbook.save(file_path)
        return file_path

    def _get_report_path(self, report_id: str) -> Path:
        reports_dir = Path(self.config.directory)
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"orders-{report_id}.xlsx"

    def _prepare_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value

        return value.astimezone(UTC).replace(tzinfo=None)
