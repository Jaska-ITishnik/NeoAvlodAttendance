from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin.views import CustomView

from bot.services.attendance import get_overall_statistics
from db.base import db
from db.models import Attendance, CourseGroup, GroupSchedule, Student


TIMEZONE = ZoneInfo("Asia/Samarkand")


class DashboardView(CustomView):
    def __init__(self) -> None:
        super().__init__(
            label="Boshqaruv paneli",
            icon="fa-solid fa-chart-line",
            path="/",
            template_path="dashboard.html",
            name="dashboard",
            add_to_menu=True,
        )

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        now = datetime.now(TIMEZONE)
        today = now.date()
        active_groups = db.scalar(
            select(func.count(CourseGroup.id)).where(CourseGroup.is_active.is_(True))
        ) or 0
        active_students = db.scalar(
            select(func.count(Student.id)).where(Student.is_active.is_(True))
        ) or 0
        today_lessons = db.scalar(
            select(func.count(GroupSchedule.id)).join(CourseGroup).where(
                GroupSchedule.is_active.is_(True),
                CourseGroup.is_active.is_(True),
                GroupSchedule.weekday == now.weekday(),
            )
        ) or 0
        today_attendance = db.execute(
            select(
                func.sum(case((Attendance.status == "present", 1), else_=0)),
                func.sum(case((Attendance.status == "absent", 1), else_=0)),
            ).where(Attendance.lesson_date == today)
        ).one()
        present = int(today_attendance[0] or 0)
        absent = int(today_attendance[1] or 0)
        total = present + absent
        today_percent = round(present * 100 / total, 1) if total else 0.0

        summaries = get_overall_statistics()
        ranked_groups = sorted(
            (item for item in summaries if item.total),
            key=lambda item: (-item.percent, item.group_name),
        )

        return templates.TemplateResponse(
            request=request,
            name=self.template_path,
            context={
                "title": "Boshqaruv paneli",
                "now": now,
                "active_groups": active_groups,
                "active_students": active_students,
                "today_lessons": today_lessons,
                "today_present": present,
                "today_absent": absent,
                "today_percent": today_percent,
                "group_summaries": ranked_groups[:8],
            },
        )
