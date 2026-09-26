from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles
from app.schemas.capabilities import DelayPropagationResponse, OperationalRiskResponse
from app.services.capability_service import unavailable_capability

router = APIRouter()


@router.get(
    "/trains/{train_number}/delay-propagation",
    response_model=DelayPropagationResponse,
)
async def get_delay_propagation(
    train_number: str,
    current_user: dict = Depends(require_roles("STAFF", "ADMIN")),
):
    return DelayPropagationResponse(**unavailable_capability("Delay propagation", train_number))


@router.get(
    "/trains/{train_number}/operational-risk",
    response_model=OperationalRiskResponse,
)
async def get_operational_risk(
    train_number: str,
    current_user: dict = Depends(require_roles("STAFF", "ADMIN")),
):
    return OperationalRiskResponse(**unavailable_capability("Operational risk analysis", train_number))
