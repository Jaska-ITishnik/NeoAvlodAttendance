from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
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


# class Student(TimestampMixin, Model):
#     """Bot bilan ishlaydigan admin, o'qituvchi yoki o'quvchi profili."""
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
#     username: Mapped[str | None] = mapped_column(String(64))
#     first_name: Mapped[str | None] = mapped_column(String(64))
#     last_name: Mapped[str | None] = mapped_column(String(64))
#     phone: Mapped[str | None] = mapped_column(String(30), unique=True)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# class Region(TimestampMixin, Model):
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
#
#     districts: Mapped[list["District"]] = relationship(
#         "District",
#         back_populates="region",
#         cascade="all, delete-orphan",
#     )
#     organizations: Mapped[list["Organization"]] = relationship(
#         "Organization",
#         back_populates="region",
#     )
#     students: Mapped[list["Student"]] = relationship("Student", back_populates="region")
#
#
# class District(TimestampMixin, Model):
#     __tablename__ = "districts"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     region_id: Mapped[int] = mapped_column(
#         ForeignKey("regions.id", ondelete="CASCADE"),
#         nullable=False,
#     )
#     name: Mapped[str] = mapped_column(String(100), nullable=False)
#
#     region: Mapped["Region"] = relationship("Region", back_populates="districts")
#     organizations: Mapped[list["Organization"]] = relationship(
#         "Organization",
#         back_populates="district",
#     )
#     students: Mapped[list["Student"]] = relationship("Student", back_populates="district")
#
#     __table_args__ = (
#         UniqueConstraint("region_id", "name", name="districts_region_name_unique"),
#     )


# class Organization(TimestampMixin, Model):
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     name: Mapped[str] = mapped_column(String(255), nullable=False)
#     short_name: Mapped[str | None] = mapped_column(String(100))
#     region_id: Mapped[int | None] = mapped_column(
#         ForeignKey("regions.id", ondelete="SET NULL")
#     )
#     district_id: Mapped[int | None] = mapped_column(
#         ForeignKey("districts.id", ondelete="SET NULL")
#     )
#     address: Mapped[str | None] = mapped_column(String(255))
#     phone: Mapped[str | None] = mapped_column(String(30))
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
#
#     region: Mapped["Region | None"] = relationship(
#         "Region",
#         back_populates="organizations",
#     )
#     district: Mapped["District | None"] = relationship(
#         "District",
#         back_populates="organizations",
#     )
#     teachers: Mapped[list["Teacher"]] = relationship(
#         "Teacher",
#         back_populates="organization",
#     )
#     students: Mapped[list["Student"]] = relationship(
#         "Student",
#         back_populates="organization",
#     )
#     courses: Mapped[list["Course"]] = relationship(
#         "Course",
#         back_populates="organization",
#     )
#
#     __table_args__ = (
#         UniqueConstraint(
#             "name",
#             "district_id",
#             name="organizations_name_district_unique",
#         ),
#     )


# class Teacher(TimestampMixin, Model):
#     __tablename__ = "teachers"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     user_id: Mapped[int | None] = mapped_column(
#         ForeignKey("telegram_users.id", ondelete="SET NULL"),
#         unique=True,
#     )
#     organization_id: Mapped[int | None] = mapped_column(
#         ForeignKey("organizations.id", ondelete="SET NULL")
#     )
#     first_name: Mapped[str] = mapped_column(String(64), nullable=False)
#     last_name: Mapped[str] = mapped_column(String(64), nullable=False)
#     middle_name: Mapped[str | None] = mapped_column(String(64))
#     phone: Mapped[str | None] = mapped_column(String(30), unique=True)
#     photo_url: Mapped[str | None] = mapped_column(Text)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
#
#     user: Mapped["Student | None"] = relationship(
#         "Student",
#         back_populates="teacher_profile",
#     )
#     organization: Mapped["Organization | None"] = relationship(
#         "Organization",
#         back_populates="teachers",
#     )
#     courses: Mapped[list["Course"]] = relationship("Course", back_populates="teacher")
#     attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(
#         "AttendanceSession",
#         back_populates="started_by",
#     )
#     marked_records: Mapped[list["AttendanceRecord"]] = relationship(
#         "AttendanceRecord",
#         back_populates="marked_by",
#     )
#
#     @property
#     def full_name(self) -> str:
#         parts = (self.last_name, self.first_name, self.middle_name)
#         return " ".join(part for part in parts if part)


class Student(TimestampMixin, Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL")
    )
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL")
    )
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(64))
    gender: Mapped[str | None] = mapped_column(String(15))
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    parent_phone: Mapped[str | None] = mapped_column(String(30))
    pinfl: Mapped[str | None] = mapped_column(String(14), unique=True)
    document_number: Mapped[str | None] = mapped_column(String(30), unique=True)
    photo_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["Student | None"] = relationship(
        "Student",
        back_populates="student_profile",
    )
    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        back_populates="students",
    )
    region: Mapped["Region | None"] = relationship("Region", back_populates="students")
    district: Mapped["District | None"] = relationship(
        "District",
        back_populates="students",
    )
    enrollments: Mapped[list["StudentEnrollment"]] = relationship(
        "StudentEnrollment",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "gender IS NULL OR gender IN ('male', 'female', 'other')",
            name="students_gender_check",
        ),
    )

    @property
    def full_name(self) -> str:
        parts = (self.last_name, self.first_name, self.middle_name)
        return " ".join(part for part in parts if part)


class CourseCategory(TimestampMixin, Model):
    __tablename__ = "course_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="category")


class Course(TimestampMixin, Model):
    """To'garak yoki qo'shimcha mashg'ulot."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL")
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_categories.id", ondelete="SET NULL")
    )
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        back_populates="courses",
    )
    category: Mapped["CourseCategory | None"] = relationship(
        "CourseCategory",
        back_populates="courses",
    )
    teacher: Mapped["Teacher | None"] = relationship("Teacher", back_populates="courses")
    schedules: Mapped[list["CourseSchedule"]] = relationship(
        "CourseSchedule",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["StudentEnrollment"]] = relationship(
        "StudentEnrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(
        "AttendanceSession",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'completed', 'cancelled')",
            name="courses_status_check",
        ),
        CheckConstraint(
            "capacity IS NULL OR capacity > 0",
            name="courses_capacity_positive_check",
        ),
    )


class StudentEnrollment(TimestampMixin, Model):
    __tablename__ = "student_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrolled_at: Mapped[date] = mapped_column(
        Date,
        server_default=func.current_date(),
        nullable=False,
    )
    left_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="enrollments_student_course_unique",
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'cancelled')",
            name="student_enrollments_status_check",
        ),
    )


class CourseSchedule(TimestampMixin, Model):
    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="schedules")
    attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(
        "AttendanceSession",
        back_populates="schedule",
    )

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "weekday",
            "start_time",
            name="course_schedules_course_weekday_time_unique",
        ),
        CheckConstraint(
            "weekday BETWEEN 0 AND 6",
            name="course_schedules_weekday_check",
        ),
        CheckConstraint("start_time < end_time", name="course_schedules_time_check"),
    )


class AttendanceSession(TimestampMixin, Model):
    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_schedules.id", ondelete="SET NULL")
    )
    started_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="opened", nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="attendance_sessions",
    )
    schedule: Mapped["CourseSchedule | None"] = relationship(
        "CourseSchedule",
        back_populates="attendance_sessions",
    )
    started_by: Mapped["Teacher | None"] = relationship(
        "Teacher",
        back_populates="attendance_sessions",
    )
    records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "schedule_id",
            "lesson_date",
            name="attendance_sessions_course_schedule_date_unique",
        ),
        CheckConstraint(
            "status IN ('opened', 'closed', 'cancelled')",
            name="attendance_sessions_status_check",
        ),
    )


class AttendanceRecord(TimestampMixin, Model):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    marked_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    marked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comment: Mapped[str | None] = mapped_column(Text)

    session: Mapped["AttendanceSession"] = relationship(
        "AttendanceSession",
        back_populates="records",
    )
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendance_records",
    )
    marked_by: Mapped["Teacher | None"] = relationship(
        "Teacher",
        back_populates="marked_records",
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="attendance_records_unique",
        ),
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="attendance_records_status_check",
        ),
    )
