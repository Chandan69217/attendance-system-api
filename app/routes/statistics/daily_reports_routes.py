from fastapi import APIRouter, status, Depends, Query
from app.core.security import verify_token
from app.core.response import success_response, error_response
from app.schemas.user_schema import Role
from app.firebase.firebase_init import db
from google.cloud.firestore_v1 import Query as FSQuery
from typing import Optional


router = APIRouter()


@router.get("/list", status_code=status.HTTP_200_OK)
def get_daily_reports(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: dict = Depends(verify_token)
):
    """
    Return the most recent N daily attendance reports.
    Only accessible by admin.
    """
    if current_user.get("role") != Role.admin:
        return error_response(message="Only admin can access daily reports")

    docs = (
        db.collection("daily_reports")
        .order_by("date", direction=FSQuery.DESCENDING)
        .limit(limit)
        .stream()
    )

    reports = [doc.to_dict() for doc in docs]

    return success_response(
        message=f"{len(reports)} daily report(s) fetched",
        data=reports
    )


@router.get("/{date}", status_code=status.HTTP_200_OK)
def get_report_by_date(
    date: str,
    current_user: dict = Depends(verify_token)
):
    """
    Return a single daily report by date (YYYY-MM-DD).
    Only accessible by admin.
    """
    if current_user.get("role") != Role.admin:
        return error_response(message="Only admin can access daily reports")

    doc = db.collection("daily_reports").document(date).get()

    if not doc.exists:
        return error_response(message=f"No report found for {date}")

    return success_response(
        message="Report fetched successfully",
        data=doc.to_dict()
    )
