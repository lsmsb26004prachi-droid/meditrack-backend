from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from schemas import MedicalReport, MedicalReportCreate, MedicalReportUpdate

router = APIRouter(prefix="/medical-reports", tags=["Medical reports"])


@router.post("/", response_model=MedicalReport, status_code=201)
def create_report(
    report: MedicalReportCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = models.MedicalReport(user_id=user.id, **report.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return MedicalReport.model_validate(row, from_attributes=True)


@router.get("/", response_model=list[MedicalReport])
def list_reports(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(models.MedicalReport)
        .where(models.MedicalReport.user_id == user.id)
        .order_by(models.MedicalReport.report_date)
    ).all()
    return [MedicalReport.model_validate(row, from_attributes=True) for row in rows]


@router.patch("/{report_id}", response_model=MedicalReport)
def update_report(
    report_id: int,
    updates: MedicalReportUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(models.MedicalReport).where(
            models.MedicalReport.id == report_id,
            models.MedicalReport.user_id == user.id,
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")

    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return MedicalReport.model_validate(row, from_attributes=True)