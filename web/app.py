from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette_admin import I18nConfig, TimezoneConfig
from starlette_admin.contrib.sqla import Admin

from config import settings
from db import Attendance, CourseGroup, GroupSchedule, GroupStudent, Student
from db.base import db
from web.dashboard import DashboardView
from web.provider import UsernameAndPasswordProvider
from web.views import (
    AttendanceView,
    CourseGroupView,
    GroupScheduleView,
    GroupStudentView,
    StudentView,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "web" / "templates"
STATICS_DIR = PROJECT_ROOT / "web" / "static"

if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY admin sessiyasi uchun sozlanishi shart")


async def root_redirect(request: Request) -> RedirectResponse:
    return RedirectResponse(request.url_for("admin:index"), status_code=302)


app = Starlette(
    debug=False,
    routes=[Route("/", root_redirect, name="home")],
    middleware=[
        Middleware(
            SessionMiddleware,
            secret_key=settings.SECRET_KEY,
            same_site="lax",
            https_only=settings.session_https_only,
            max_age=60 * 60 * 12,
        )
    ],
)

admin = Admin(
    engine=db._engine,
    title="Neo Avlod · Davomat",
    base_url="/admin",
    route_name="admin",
    templates_dir=str(TEMPLATES_DIR),
    statics_dir=str(STATICS_DIR),
    index_view=DashboardView(),
    auth_provider=UsernameAndPasswordProvider(),
    i18n_config=I18nConfig(default_locale="uz"),
    timezone_config=TimezoneConfig(
        default_timezone="Asia/Samarkand",
        database_timezone="Asia/Samarkand",
        use_user_locale_timezone=False,
    ),
    logo_url="/admin/statics/images/logo.svg",
    login_logo_url="/admin/statics/images/logo.svg",
    favicon_url="/admin/statics/images/favicon.svg",
)

admin.add_view(
    CourseGroupView(
        CourseGroup,
        icon="fa-solid fa-people-group",
        name="Guruh",
        label="Guruhlar",
        identity="groups",
    )
)
admin.add_view(
    StudentView(
        Student,
        icon="fa-solid fa-user-graduate",
        name="O‘quvchi",
        label="O‘quvchilar",
        identity="students",
    )
)
admin.add_view(
    GroupScheduleView(
        GroupSchedule,
        icon="fa-solid fa-calendar-days",
        name="Dars jadvali",
        label="Dars jadvallari",
        identity="schedules",
    )
)
admin.add_view(
    GroupStudentView(
        GroupStudent,
        icon="fa-solid fa-user-plus",
        name="Guruh a’zosi",
        label="Guruh a’zolari",
        identity="enrollments",
    )
)
admin.add_view(
    AttendanceView(
        Attendance,
        icon="fa-solid fa-clipboard-check",
        name="Davomat",
        label="Davomat yozuvlari",
        identity="attendance",
    )
)

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="0.0.0.0", port=8088, reload=False)
