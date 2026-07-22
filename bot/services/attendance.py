from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from db.base import db
from db.models import Attendance, CourseGroup, GroupSchedule, GroupStudent, Student
from bot.services.rules import (
    EVEN_WEEKDAYS,
    ODD_WEEKDAYS,
    attendance_percent,
    period_weekdays,
    time_in_lesson,
)


APP_TIMEZONE = ZoneInfo("Asia/Samarkand")


@dataclass(slots=True)
class GroupDetails:
    group: CourseGroup
    schedules: list[GroupSchedule]
    student_count: int


@dataclass(slots=True)
class AttendanceSnapshot:
    group: CourseGroup
    schedule: GroupSchedule
    students: list[Student]
    present_student_ids: set[int]


@dataclass(slots=True)
class GroupSummary:
    group_id: int
    group_name: str
    course_name: str
    lessons: int = 0
    present: int = 0
    absent: int = 0

    @property
    def total(self) -> int:
        return self.present + self.absent

    @property
    def percent(self) -> float:
        return attendance_percent(self.present, self.absent)


@dataclass(slots=True)
class StudentAttendanceSummary:
    student_id: int
    full_name: str
    present: int = 0
    absent: int = 0

    @property
    def total(self) -> int:
        return self.present + self.absent

    @property
    def percent(self) -> float:
        return attendance_percent(self.present, self.absent)


def _weekdays(period: str) -> tuple[int, ...]:
    return period_weekdays(period)


def list_groups(period: str) -> list[CourseGroup]:
    statement = (
        select(CourseGroup)
        .join(GroupSchedule, GroupSchedule.group_id == CourseGroup.id)
        .where(
            CourseGroup.is_active.is_(True),
            GroupSchedule.is_active.is_(True),
            GroupSchedule.weekday.in_(_weekdays(period)),
        )
        .distinct()
        .order_by(CourseGroup.name)
    )
    return list(db.execute(statement).scalars().all())


def get_group_details(group_id: int) -> GroupDetails | None:
    group = db.scalar(
        select(CourseGroup).where(
            CourseGroup.id == group_id,
            CourseGroup.is_active.is_(True),
        )
    )
    if group is None:
        return None

    schedules = list(
        db.execute(
            select(GroupSchedule)
            .where(
                GroupSchedule.group_id == group_id,
                GroupSchedule.is_active.is_(True),
            )
            .order_by(GroupSchedule.weekday, GroupSchedule.start_time)
        ).scalars().all()
    )
    student_count = len(
        db.execute(
            select(GroupStudent.id)
            .join(Student, Student.id == GroupStudent.student_id)
            .where(
                GroupStudent.group_id == group_id,
                GroupStudent.is_active.is_(True),
                Student.is_active.is_(True),
            )
        ).all()
    )
    return GroupDetails(group=group, schedules=schedules, student_count=student_count)


def find_current_schedule(
    group_id: int,
    now: datetime | None = None,
) -> tuple[GroupSchedule | None, str | None]:
    local_now = now.astimezone(APP_TIMEZONE) if now else datetime.now(APP_TIMEZONE)
    schedules = list(
        db.execute(
            select(GroupSchedule)
            .join(CourseGroup, CourseGroup.id == GroupSchedule.group_id)
            .where(
                GroupSchedule.group_id == group_id,
                GroupSchedule.is_active.is_(True),
                CourseGroup.is_active.is_(True),
                GroupSchedule.weekday == local_now.weekday(),
            )
            .order_by(GroupSchedule.start_time)
        ).scalars().all()
    )
    if not schedules:
        return None, "Bugun bu guruhda dars yo‘q."

    current_time = local_now.time().replace(tzinfo=None)
    for schedule in schedules:
        if time_in_lesson(current_time, schedule.start_time, schedule.end_time):
            return schedule, None

    intervals = ", ".join(
        f"{item.start_time:%H:%M}–{item.end_time:%H:%M}" for item in schedules
    )
    return None, f"Hozir dars vaqti emas. Bugungi vaqt: {intervals}."


def get_attendance_snapshot(
    group_id: int,
    schedule: GroupSchedule,
    lesson_date: date,
) -> AttendanceSnapshot | None:
    if schedule.group_id != group_id or not schedule.is_active:
        return None
    group = db.scalar(
        select(CourseGroup).where(
            CourseGroup.id == group_id,
            CourseGroup.is_active.is_(True),
        )
    )
    if group is None:
        return None

    students = list(
        db.execute(
            select(Student)
            .join(GroupStudent, GroupStudent.student_id == Student.id)
            .where(
                GroupStudent.group_id == group_id,
                GroupStudent.is_active.is_(True),
                Student.is_active.is_(True),
            )
            .order_by(Student.last_name, Student.first_name)
        ).scalars().all()
    )
    existing = db.execute(
        select(Attendance.student_id, Attendance.status).where(
            Attendance.schedule_id == schedule.id,
            Attendance.lesson_date == lesson_date,
        )
    ).all()
    present_ids = {student_id for student_id, status in existing if status == "present"}
    return AttendanceSnapshot(group, schedule, students, present_ids)


def save_attendance(
    schedule_id: int,
    lesson_date: date,
    students: list[Student],
    present_student_ids: set[int],
    admin_telegram_id: int,
) -> None:
    existing = {
        item.student_id: item
        for item in db.execute(
            select(Attendance).where(
                Attendance.schedule_id == schedule_id,
                Attendance.lesson_date == lesson_date,
            )
        ).scalars().all()
    }
    try:
        for student in students:
            status = "present" if student.id in present_student_ids else "absent"
            record = existing.get(student.id)
            if record is None:
                db.add(
                    Attendance(
                        schedule_id=schedule_id,
                        student_id=student.id,
                        lesson_date=lesson_date,
                        status=status,
                        marked_by_telegram_id=admin_telegram_id,
                    )
                )
            else:
                record.status = status
                record.marked_by_telegram_id = admin_telegram_id
                record.marked_at = datetime.now(APP_TIMEZONE)
        db.commit()
    except Exception:
        db.rollback()
        raise


def _statistics_rows(since: date, group_id: int | None = None):
    statement = (
        select(
            Attendance.schedule_id,
            Attendance.lesson_date,
            Attendance.student_id,
            Attendance.status,
            GroupSchedule.group_id,
        )
        .join(GroupSchedule, GroupSchedule.id == Attendance.schedule_id)
        .where(Attendance.lesson_date >= since)
    )
    if group_id is not None:
        statement = statement.where(GroupSchedule.group_id == group_id)
    return db.execute(statement).all()


def get_overall_statistics(days: int = 30) -> list[GroupSummary]:
    since = datetime.now(APP_TIMEZONE).date() - timedelta(days=days - 1)
    groups = list(
        db.execute(
            select(CourseGroup)
            .where(CourseGroup.is_active.is_(True))
            .order_by(CourseGroup.name)
        ).scalars().all()
    )
    summaries = {
        group.id: GroupSummary(group.id, group.name, group.course_name)
        for group in groups
    }
    lesson_keys: dict[int, set[tuple[int, date]]] = defaultdict(set)
    for schedule_id, lesson_date, _student_id, status, group_id in _statistics_rows(since):
        summary = summaries.get(group_id)
        if summary is None:
            continue
        lesson_keys[group_id].add((schedule_id, lesson_date))
        if status == "present":
            summary.present += 1
        elif status == "absent":
            summary.absent += 1
    for group_id, keys in lesson_keys.items():
        summaries[group_id].lessons = len(keys)
    return list(summaries.values())


def get_group_statistics(
    group_id: int,
    days: int = 30,
) -> tuple[GroupSummary, list[StudentAttendanceSummary]] | None:
    group = db.scalar(select(CourseGroup).where(CourseGroup.id == group_id))
    if group is None:
        return None
    since = datetime.now(APP_TIMEZONE).date() - timedelta(days=days - 1)
    summary = GroupSummary(group.id, group.name, group.course_name)
    lesson_keys: set[tuple[int, date]] = set()
    student_counts: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for schedule_id, lesson_date, student_id, status, _group_id in _statistics_rows(since, group_id):
        lesson_keys.add((schedule_id, lesson_date))
        if status == "present":
            summary.present += 1
            student_counts[student_id][0] += 1
        elif status == "absent":
            summary.absent += 1
            student_counts[student_id][1] += 1
    summary.lessons = len(lesson_keys)

    students = list(
        db.execute(
            select(Student)
            .join(GroupStudent, GroupStudent.student_id == Student.id)
            .where(GroupStudent.group_id == group_id, GroupStudent.is_active.is_(True))
            .order_by(Student.last_name, Student.first_name)
        ).scalars().all()
    )
    details = [
        StudentAttendanceSummary(
            student_id=student.id,
            full_name=student.full_name,
            present=student_counts[student.id][0],
            absent=student_counts[student.id][1],
        )
        for student in students
    ]
    details.sort(key=lambda item: (item.percent, -item.total, item.full_name))
    return summary, details
