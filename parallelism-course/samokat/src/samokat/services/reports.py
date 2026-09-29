from samokat.application.dto import ReportCreateData, ReportData
from samokat.domain.enums import ReportStatus
from samokat.infrastructure.postgres.manager import DatabaseManager
from samokat.infrastructure.reports.excel import OrdersReportExcelWriter
from samokat.infrastructure.tasks.publisher import TaskPublisher


class ReportService:
    def __init__(
        self,
        db: DatabaseManager,
        excel_writer: OrdersReportExcelWriter,
        task_publisher: TaskPublisher,
    ) -> None:
        self.db = db
        self.excel_writer = excel_writer
        self.task_publisher = task_publisher

    async def create_orders_report(self, user_id: int) -> ReportCreateData:
        report_id = await self.db.reports.create_order_report(user_id)
        await self.db.commit()

        await self.task_publisher.schedule_order_report(report_id)

        return ReportCreateData(
            report_id=report_id,
            status=ReportStatus.PENDING,
        )

    async def get_report(self, report_id: str) -> ReportData | None:
        return await self.db.reports.get_report(report_id)

    async def generate_orders_report(self, report_id: str) -> None:
        report = await self.db.reports.get_report(report_id)

        if report is None:
            return

        await self.db.reports.set_processing(report_id)
        await self.db.commit()

        try:
            rows = await self.db.orders.get_report_rows(report.user_id)
            file_path = self.excel_writer.write(report_id, rows)
            await self.db.reports.set_completed(report_id, str(file_path))
            await self.db.commit()
        except Exception as exc:
            await self.db.reports.set_failed(report_id, str(exc))
            await self.db.commit()
            raise

    async def run_bg_tasks(self):
        self.task_publisher.schedule_20_async_tasks()
