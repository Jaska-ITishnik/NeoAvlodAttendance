from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


COMMON_LABELS = {
    "id": "ID",
    "created_at": "Yaratilgan vaqt",
    "updated_at": "Yangilangan vaqt",
    "is_active": "Faol",
    "group": "Guruh",
    "group_id": "Guruh ID",
    "student": "O‘quvchi",
    "student_id": "O‘quvchi ID",
    "schedule": "Dars jadvali",
    "schedule_id": "Jadval ID",
}


class AttendanceModelView(ModelView):
    page_size = 25
    page_size_options = [10, 25, 50, 100]
    responsive_table = True
    search_builder = True
    column_visibility = True
    save_state = True
    fields_default_sort = [("id", True)]
    exclude_fields_from_create = ["id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "created_at", "updated_at"]
    field_labels: dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {**COMMON_LABELS, **self.field_labels}
        for field in self.fields:
            if field.name in labels:
                field.label = labels[field.name]


class StudentView(AttendanceModelView):
    fields = [
        "id",
        "last_name",
        "first_name",
        "parent_telegram_id",
        "is_active",
        "created_at",
        "updated_at",
    ]
    searchable_fields = ["first_name", "last_name", "parent_telegram_id"]
    sortable_fields = ["id", "first_name", "last_name", "is_active", "created_at"]
    field_labels = {
        "first_name": "Ism",
        "last_name": "Familiya",
        "parent_telegram_id": "Ota-ona Telegram ID",
    }

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors = {}
        if not str(data.get("first_name") or "").strip():
            errors["first_name"] = "Ism kiritilishi shart"
        if not str(data.get("last_name") or "").strip():
            errors["last_name"] = "Familiya kiritilishi shart"
        if errors:
            raise FormValidationError(errors)


class CourseGroupView(AttendanceModelView):
    fields = ["id", "name", "course_name", "is_active", "created_at", "updated_at"]
    searchable_fields = ["name", "course_name"]
    sortable_fields = ["id", "name", "course_name", "is_active", "created_at"]
    field_labels = {"name": "Guruh nomi", "course_name": "Kurs nomi"}

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors = {}
        if not str(data.get("name") or "").strip():
            errors["name"] = "Guruh nomi kiritilishi shart"
        if not str(data.get("course_name") or "").strip():
            errors["course_name"] = "Kurs nomi kiritilishi shart"
        if errors:
            raise FormValidationError(errors)


class GroupScheduleView(AttendanceModelView):
    fields = [
        "id",
        "group",
        "weekday",
        "start_time",
        "end_time",
        "is_active",
        "created_at",
        "updated_at",
    ]
    searchable_fields = ["weekday"]
    sortable_fields = ["id", "weekday", "start_time", "end_time", "is_active"]
    field_labels = {
        "weekday": "Hafta kuni (0=Dushanba, 6=Yakshanba)",
        "start_time": "Boshlanish vaqti",
        "end_time": "Tugash vaqti",
    }

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors = {}
        weekday = data.get("weekday")
        if weekday is None or not 0 <= weekday <= 6:
            errors["weekday"] = "Hafta kuni 0 dan 6 gacha bo‘lishi kerak"
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if start_time and end_time and start_time >= end_time:
            errors["end_time"] = "Tugash vaqti boshlanish vaqtidan keyin bo‘lishi kerak"
        if errors:
            raise FormValidationError(errors)


class GroupStudentView(AttendanceModelView):
    fields = [
        "id",
        "group",
        "student",
        "joined_on",
        "is_active",
        "created_at",
        "updated_at",
    ]
    searchable_fields = ["joined_on"]
    sortable_fields = ["id", "joined_on", "is_active", "created_at"]
    field_labels = {"joined_on": "Guruhga qo‘shilgan sana"}


class AttendanceView(AttendanceModelView):
    fields = [
        "id",
        "schedule",
        "student",
        "lesson_date",
        "status",
        "marked_at",
        "marked_by_telegram_id",
        "note",
        "parent_notified_at",
        "notification_error",
        "admin_latitude",
        "admin_longitude",
        "distance_from_center_meters",
        "created_at",
        "updated_at",
    ]
    searchable_fields = ["status", "note", "marked_by_telegram_id"]
    sortable_fields = ["id", "lesson_date", "status", "marked_at"]
    exclude_fields_from_list = [
        "note",
        "parent_notified_at",
        "notification_error",
        "admin_latitude",
        "admin_longitude",
        "distance_from_center_meters",
        "created_at",
        "updated_at",
    ]
    field_labels = {
        "lesson_date": "Dars sanasi",
        "status": "Davomat holati",
        "marked_at": "Belgilangan vaqt",
        "marked_by_telegram_id": "Belgilagan admin Telegram ID",
        "note": "Izoh",
        "parent_notified_at": "Ota-onaga xabar berilgan vaqt",
        "notification_error": "Xabarnoma xatosi",
        "admin_latitude": "Admin kengligi",
        "admin_longitude": "Admin uzunligi",
        "distance_from_center_meters": "Markazgacha masofa (metr)",
    }

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        allowed_statuses = {"present", "absent", "late", "excused"}
        if data.get("status") not in allowed_statuses:
            raise FormValidationError(
                {"status": "Holat: present, absent, late yoki excused bo‘lishi kerak"}
            )
