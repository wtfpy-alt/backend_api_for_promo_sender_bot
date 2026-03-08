from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from routes.database import Promotion, get_db  # ← your database.py

router = APIRouter(prefix="/promotions", tags=["promotions"])


# ────────────────────────────────────────────────
# Models for request/response
# ────────────────────────────────────────────────
class PromotionCreate(BaseModel):
    user_id: int
    text: str  # consistent with model


class PromotionOut(BaseModel):
    id: int
    user_id: int
    text: str
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None


# ────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────
@router.post("/create")
async def create_promotion(
    promo_data: PromotionCreate,  # ← use body instead of query params
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new promotion (use JSON body)
    """
    promo = Promotion(
        user_id=promo_data.user_id,
        text=promo_data.text,
        status="pending"
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)

    return {"ok": True, "promotion_id": promo.id}


@router.get("/pending", response_model=List[PromotionOut])
async def get_pending_promotions(db: AsyncSession = Depends(get_db)):
    """
    Get all pending promotions
    """
    result = await db.execute(
        select(Promotion).where(Promotion.status == "pending")
    )
    promos = result.scalars().all()
    return promos


@router.post("/approve")
async def approve_promotion(
    promotion_id: int = Query(..., description="Promotion ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a promotion by ID (query param)
    """
    result = await db.execute(
        select(Promotion).where(Promotion.id == promotion_id)
    )
    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    promo.status = "approved"
    promo.approved_at = datetime.utcnow()  # or datetime.now(datetime.UTC) in Py 3.11+

    await db.commit()

    return {"ok": True}


@router.post("/reject")
async def reject_promotion(
    promotion_id: int = Query(..., description="Promotion ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a promotion by ID (query param)
    """
    result = await db.execute(
        select(Promotion).where(Promotion.id == promotion_id)
    )
    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    promo.status = "rejected"
    promo.rejected_at = datetime.utcnow()

    await db.commit()

    return {"ok": True}


@router.get("", response_model=List[PromotionOut])
async def get_promotions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all promotions (paginated, newest first)
    """
    result = await db.execute(
        select(Promotion)
        .order_by(Promotion.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    promotions = result.scalars().all()
    return promotions
