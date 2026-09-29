from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import insert, select, update

from samokat.application.dto import ReportData
from samokat.domain.enums import ReportStatus
from samokat.infrastructure.postgres.models import ReportModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class ReportRepo(BaseRepo):
    async def create_order_report(self, user_id: int) -> str:
        report_id = str(uuid4())
        query = insert(ReportModel).values(
            id=report_id,
            user_id=user_id,
            status=ReportStatus.PENDING,
        )

        await self.session.execute(query)
        return report_id

    async def get_report(self, report_id: str) -> ReportData | None:
        query = select(ReportModel).where(ReportModel.id == report_id)

        resp = await self.session.scalars(query)
        report = resp.one_or_none()

        if report is None:
            return None

        return ReportData(
            id=report.id,
            user_id=report.user_id,
            status=report.status,
            file_path=report.file_path,
            error=report.error,
            created_at=report.created_at,
            updated_at=report.updated_at,
            completed_at=report.completed_at,
        )

    async def set_processing(self, report_id: str) -> None:
        query = (
            update(ReportModel)
            .where(ReportModel.id == report_id)
            .values(
                status=ReportStatus.PROCESSING,
                updated_at=datetime.now(UTC),
                error=None,
            )
        )

        await self.session.execute(query)

    async def set_completed(self, report_id: str, file_path: str) -> None:
        now = datetime.now(UTC)
        query = (
            update(ReportModel)
            .where(ReportModel.id == report_id)
            .values(
                status=ReportStatus.COMPLETED,
                file_path=file_path,
                updated_at=now,
                completed_at=now,
                error=None,
            )
        )

        await self.session.execute(query)

    async def set_failed(self, report_id: str, error: str) -> None:
        query = (
            update(ReportModel)
            .where(ReportModel.id == report_id)
            .values(
                status=ReportStatus.FAILED,
                error=error,
                updated_at=datetime.now(UTC),
            )
        )

        await self.session.execute(query)
