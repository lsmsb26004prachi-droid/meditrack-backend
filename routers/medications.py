from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from schemas import (
    Medicine,
    MedicineCreate,
    MedicineUpdate,
    MedicationLog,
    MedicationLogCreate,
    SideEffect,
    SideEffectCreate,
)

router = APIRouter(prefix="/medications", tags=["Medications"])


def to_utc_naive(value: datetime) -> datetime:
    """MySQL stores plain date-times, so convert everything to UTC first."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def get_owned_medicine(medicine_id: int, user: models.User, db: Session) -> models.Medicine:
    """Fetch a medicine and confirm it belongs to the requesting user, or 404."""
    medicine = db.get(models.Medicine, medicine_id)
    if medicine is None or medicine.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


# ---------- Medicines ----------

@router.post("/", response_model=Medicine, status_code=201)
def create_medicine(
    medicine: MedicineCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = models.Medicine(user_id=user.id, **medicine.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return Medicine.model_validate(row, from_attributes=True)


@router.get("/", response_model=list[Medicine])
def list_medicines(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(models.Medicine)
        .where(models.Medicine.user_id == user.id)
        .order_by(models.Medicine.created_at)
    ).all()
    return [Medicine.model_validate(row, from_attributes=True) for row in rows]


@router.patch("/{medicine_id}", response_model=Medicine)
def update_medicine(
    medicine_id: int,
    updates: MedicineUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_medicine(medicine_id, user, db)
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return Medicine.model_validate(row, from_attributes=True)


@router.delete("/{medicine_id}", status_code=204)
def delete_medicine(
    medicine_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_medicine(medicine_id, user, db)
    # MySQL will not delete a medicine while logs or side effects still point at it.
    db.execute(
        delete(models.MedicationLog).where(models.MedicationLog.medicine_id == medicine_id)
    )
    db.execute(
        delete(models.SideEffect).where(models.SideEffect.medicine_id == medicine_id)
    )
    db.delete(row)
    db.commit()


# ---------- Medication logs (taken / missed) ----------

@router.post("/logs", response_model=MedicationLog, status_code=201)
def create_log(
    log: MedicationLogCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_medicine(log.medicine_id, user, db)  # 404s if not this user's medicine
    row = db.scalar(
        select(models.MedicationLog).where(
            models.MedicationLog.user_id == user.id,
            models.MedicationLog.medicine_id == log.medicine_id,
            models.MedicationLog.log_date == log.log_date,
        )
    )
    if row is None:
        row = models.MedicationLog(user_id=user.id, **log.model_dump())
        db.add(row)
    else:
        row.taken = log.taken  # one row per medicine per day: update it
    db.commit()
    db.refresh(row)
    return MedicationLog.model_validate(row, from_attributes=True)


@router.get("/logs", response_model=list[MedicationLog])
def list_logs(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(models.MedicationLog)
        .where(models.MedicationLog.user_id == user.id)
        .order_by(models.MedicationLog.log_date)
    ).all()
    return [MedicationLog.model_validate(row, from_attributes=True) for row in rows]


# ---------- Side effects ----------

@router.post("/side-effects", response_model=SideEffect, status_code=201)
def create_side_effect(
    side_effect: SideEffectCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_medicine(side_effect.medicine_id, user, db)  # 404s if not this user's medicine
    data = side_effect.model_dump()
    data["reported_at"] = to_utc_naive(data["reported_at"])
    row = models.SideEffect(user_id=user.id, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SideEffect.model_validate(row, from_attributes=True)


@router.get("/side-effects", response_model=list[SideEffect])
def list_side_effects(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(models.SideEffect)
        .where(models.SideEffect.user_id == user.id)
        .order_by(models.SideEffect.reported_at)
    ).all()
    return [SideEffect.model_validate(row, from_attributes=True) for row in rows]