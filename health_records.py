from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from schemas import HealthRecord, HealthRecordCreate

router = APIRouter(prefix="/health-records", tags=["Health records"])


def to_utc_naive(value: datetime) -> datetime:
    """MySQL stores plain date-times, so convert everything to UTC first."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


@router.post("/", response_model=HealthRecord, status_code=201)
def create_record(
    record: HealthRecordCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = record.model_dump()
    data["recorded_at"] = to_utc_naive(data["recorded_at"])
    row = models.HealthRecord(user_id=user.id, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return HealthRecord.model_validate(row, from_attributes=True)


@router.get("/", response_model=list[HealthRecord])
def list_records(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(models.HealthRecord)
        .where(models.HealthRecord.user_id == user.id)
        .order_by(models.HealthRecord.recorded_at)
    ).all()
    return [HealthRecord.model_validate(row, from_attributes=True) for row in rows]