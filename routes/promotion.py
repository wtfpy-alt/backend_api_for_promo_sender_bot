from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import Promotion, get_db

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.post("/create")
async def create_promotion(
    user_id: int,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    promo = Promotion(
        user_id=user_id,
        message=message,
        status="pending"
    )

    db.add(promo)
    await db.commit()

    return {"ok": True}


@router.get("/pending")
async def get_pending_promotions(db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(Promotion).where(Promotion.status == "pending")
    )

    promos = result.scalars().all()

    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "message": p.message,
            "created_at": p.created_at
        }
        for p in promos
    ]


@router.post("/{promo_id}/approve")
async def approve_promotion(
    promo_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(Promotion).where(Promotion.id == promo_id)
    )

    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(404, "Promotion not found")

    promo.status = "approved"
    promo.approved_at = datetime.utcnow()

    await db.commit()

    return {"ok": True}


@router.post("/{promo_id}/reject")
async def reject_promotion(
    promo_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(Promotion).where(Promotion.id == promo_id)
    )

    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(404, "Promotion not found")

    promo.status = "rejected"
    promo.rejected_at = datetime.utcnow()

    await db.commit()

    return {"ok": True}