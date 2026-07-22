from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Model


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Student(TimestampMixin, Model):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enrollments: Mapped[list["GroupStudent"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class CourseGroup(TimestampMixin, Model):
    __tablename__ = "course_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    course_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schedules: Mapped[list["GroupSchedule"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    students: Mapped[list["GroupStudent"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "learning_center_id",
            "name",
            name="course_groups_center_name_unique",
        ),
    )


class GroupSchedule(TimestampMixin, Model):
    """A weekly lesson slot. Weekday uses Monday=0 through Sunday=6."""

    __tablename__ = "group_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("course_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    group: Mapped["CourseGroup"] = relationship(back_populates="schedules")
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="schedule",
    )

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "weekday",
            "start_time",
            name="group_schedules_group_day_start_unique",
        ),
        CheckConstraint(
            "weekday BETWEEN 0 AND 6",
            name="group_schedules_weekday_check",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="group_schedules_time_check",
        ),
    )


class GroupStudent(TimestampMixin, Model):
    """Membership of a student in a course group."""

    __tablename__ = "group_students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("course_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_on: Mapped[date] = mapped_column(
        Date,
        server_default=func.current_date(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    group: Mapped["CourseGroup"] = relationship(back_populates="students")
    student: Mapped["Student"] = relationship(back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "student_id",
            name="group_students_group_student_unique",
        ),
    )


class Attendance(TimestampMixin, Model):
    """One student's attendance for one scheduled lesson on a specific date."""

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("group_schedules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="present",
        nullable=False,
    )
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Saved as proof that the admin was inside the center's allowed radius.
    admin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    admin_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    distance_from_center_meters: Mapped[float] = mapped_column(Float, nullable=False)

    parent_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    notification_error: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)

    schedule: Mapped["GroupSchedule"] = relationship(
        back_populates="attendance_records"
    )
    student: Mapped["Student"] = relationship(back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "student_id",
            "lesson_date",
            name="attendance_schedule_student_date_unique",
        ),
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="attendance_status_check",
        ),
        CheckConstraint(
            "admin_latitude BETWEEN -90 AND 90",
            name="attendance_latitude_check",
        ),
        CheckConstraint(
            "admin_longitude BETWEEN -180 AND 180",
            name="attendance_longitude_check",
        ),
        CheckConstraint(
            "distance_from_center_meters >= 0",
            name="attendance_distance_check",
        ),
    )
