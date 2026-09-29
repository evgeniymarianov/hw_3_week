from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from samokat.api.dependencies import UserIdDep
from samokat.application.dto import ReportCreateData, ReportData
from samokat.domain.enums import ReportStatus
from samokat.services.reports import ReportService

router = APIRouter(prefix="/reports", route_class=DishkaRoute, tags=["Отчеты"])


@router.post("/orders")
async def create_orders_report(
    user_id: UserIdDep,
    service: FromDishka[ReportService],
) -> ReportCreateData:
    return await service.create_orders_report(user_id)


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user_id: UserIdDep,
    service: FromDishka[ReportService],
) -> ReportData:
    report = await service.get_report(report_id)

    if report is None or report.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    user_id: UserIdDep,
    service: FromDishka[ReportService],
) -> FileResponse:
    report = await service.get_report(report_id)

    if report is None or report.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if report.status != ReportStatus.COMPLETED or report.file_path is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    return FileResponse(
        report.file_path,
        filename=f"orders-{report.id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


#############
## ОПАСНО! ##
#############


@router.get("/celery/test")
async def run_celery_tasks(service: FromDishka[ReportService]):
    return await service.run_bg_tasks()
