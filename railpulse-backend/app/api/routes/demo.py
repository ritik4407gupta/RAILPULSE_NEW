from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, require_roles
from app.db.mongodb import db
from app.services.demo_data_service import refresh_demo_trains, reset_demo_trains, seed_demo_trains

router = APIRouter()


@router.post("/seed")
async def seed_demo_data(current_user: dict = Depends(require_roles("STAFF", "ADMIN"))):
    result = await seed_demo_trains()
    return result


@router.post("/refresh")
async def refresh_demo_data(current_user: dict = Depends(require_roles("STAFF", "ADMIN"))):
    result = await refresh_demo_trains()
    return result


@router.post("/reset")
async def reset_demo_data(current_user: dict = Depends(require_roles("ADMIN"))):
    result = await reset_demo_trains()
    return result


@router.delete("/seed")
async def delete_demo_seed_alias(current_user: dict = Depends(require_roles("ADMIN"))):
    result = await reset_demo_trains()
    return result
