from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.db.repositories.alert_repository import list_alerts
from app.schemas.capabilities import AlertsResponse
from app.services.capability_service import alert_document_to_response, unavailable_alerts

router = APIRouter()


@router.get("", response_model=AlertsResponse)
async def get_alerts(
    train_number: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    documents = await list_alerts(train_number, limit)
    if not documents:
        return AlertsResponse(**unavailable_alerts())
    return AlertsResponse(
        status="available",
        data_source="mongodb_alerts_collection",
        alerts=[alert_document_to_response(document) for document in documents],
    )
