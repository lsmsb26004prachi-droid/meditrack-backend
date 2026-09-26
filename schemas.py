from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class HealthRecordCreate(BaseModel):
    """What the app sends when saving a daily record."""

    recorded_at: datetime
    symptoms: list[str] = []
    severity: Optional[int] = Field(default=None, ge=0, le=10)
    weight_kg: Optional[float] = Field(default=None, gt=20, lt=300)
    systolic_bp: Optional[int] = Field(default=None, ge=60, le=260)
    diastolic_bp: Optional[int] = Field(default=None, ge=30, le=160)
    heart_rate: Optional[int] = Field(default=None, ge=30, le=220)
    temperature_c: Optional[float] = Field(default=None, ge=30, le=45)
    glucose_mg_dl: Optional[float] = Field(default=None, ge=20, le=600)
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    activity: Optional[str] = None


class HealthRecord(HealthRecordCreate):
    """A saved record: everything above, plus an id."""

    id: int


class MedicalReportCreate(BaseModel):
    """What the app sends when saving a lab/medical report."""

    report_type: str = Field(min_length=1, max_length=50)
    report_date: date
    notes: str = Field(default="", max_length=1000)

    @field_validator("report_date")
    @classmethod
    def date_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("report_date cannot be in the future")
        return value


class MedicalReport(MedicalReportCreate):
    """A saved report: everything above, plus an id."""

    id: int


class MedicalReportUpdate(BaseModel):
    """What the app sends when editing a report. Every field is optional."""

    report_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    report_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("report_date")
    @classmethod
    def date_not_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value > date.today():
            raise ValueError("report_date cannot be in the future")
        return value


class MedicineCreate(BaseModel):
    """What the app sends when adding a medicine."""

    name: str = Field(min_length=1, max_length=150)
    dose: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = Field(default=None, max_length=150)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, value: Optional[date], info) -> Optional[date]:
        start = info.data.get("start_date")
        if value is not None and start is not None and value < start:
            raise ValueError("end_date cannot be before start_date")
        return value


class Medicine(MedicineCreate):
    """A saved medicine: everything above, plus an id."""

    id: int


class MedicineUpdate(BaseModel):
    """What the app sends when editing a medicine. Every field is optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    dose: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = Field(default=None, max_length=150)


class MedicationLogCreate(BaseModel):
    """What the app sends to log a day's medicine as taken or missed."""

    medicine_id: int
    log_date: date
    taken: bool = False


class MedicationLog(MedicationLogCreate):
    """A saved log entry: everything above, plus an id."""

    id: int


class SideEffectCreate(BaseModel):
    """What the app sends when reporting a side effect."""

    medicine_id: int
    description: str = Field(min_length=1, max_length=1000)
    severity: Optional[int] = Field(default=None, ge=0, le=10)
    reported_at: datetime


class SideEffect(SideEffectCreate):
    """A saved side-effect report: everything above, plus an id."""

    id: int