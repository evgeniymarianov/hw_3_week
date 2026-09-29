class TaskPublisher:
    async def schedule_order_report(self, report_id: str):
        # from samokat.infrastructure.tasks.celery_tasks import generate_order_report

        # generate_order_report.apply_async(kwargs={"report_id": report_id})
        # generate_order_report.delay(report_id)
        # from samokat.infrastructure.tasks.celery_app import celery_app
        # celery_app.send_task(name="generate_order_report", kwargs={"report_id": report_id})

        from samokat.infrastructure.tasks.taskiq_tasks import generate_order_report

        await generate_order_report.kiq(report_id)

    def schedule_20_async_tasks(self):
        from samokat.infrastructure.tasks.celery_tasks import truly_async_task

        for _ in range(200):
            truly_async_task.delay()
