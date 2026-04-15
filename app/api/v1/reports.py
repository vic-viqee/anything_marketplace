from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Report, ReportStatus, Product, Conversation
from app.schemas.schemas import ReportCreate, ReportResponse, ReportUpdate

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not any(
        [
            report_data.reported_user_id,
            report_data.reported_product_id,
            report_data.reported_conversation_id,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must report at least one of: user, product, or conversation",
        )

    if report_data.reported_user_id:
        reported_user = (
            db.query(User).filter(User.id == report_data.reported_user_id).first()
        )
        if not reported_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported user not found",
            )

    if report_data.reported_product_id:
        product = (
            db.query(Product)
            .filter(Product.id == report_data.reported_product_id)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported product not found",
            )

    if report_data.reported_conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == report_data.reported_conversation_id)
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    report = Report(
        reporter_id=current_user.id,
        reported_user_id=report_data.reported_user_id,
        reported_product_id=report_data.reported_product_id,
        reported_conversation_id=report_data.reported_conversation_id,
        reason=report_data.reason,
        description=report_data.description,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report
