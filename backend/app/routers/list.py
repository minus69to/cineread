from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.media_list import SavedItem
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/list", tags=["list"])


class SaveRequest(BaseModel):
    media_id: str
    media_type: str
    title: str
    year: int | None = None
    rating: float | None = None
    cover_url: str | None = None


class RateRequest(BaseModel):
    user_rating: float


@router.get("")
async def get_list(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedItem).where(SavedItem.user_id == user.id).order_by(SavedItem.saved_at.desc())
    )
    items = result.scalars().all()
    return {"items": [
        {
            "id": i.id,
            "media_id": i.media_id,
            "media_type": i.media_type,
            "title": i.title,
            "year": i.year,
            "rating": i.rating,
            "cover_url": i.cover_url,
            "user_rating": i.user_rating,
            "saved_at": i.saved_at.isoformat(),
        }
        for i in items
    ]}


@router.post("", status_code=201)
async def save_item(
    req: SaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(SavedItem).where(
            SavedItem.user_id == user.id,
            SavedItem.media_id == req.media_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already saved")

    item = SavedItem(
        user_id=user.id,
        media_id=req.media_id,
        media_type=req.media_type,
        title=req.title,
        year=req.year,
        rating=req.rating,
        cover_url=req.cover_url,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "media_id": item.media_id}


@router.patch("/{item_id}/rate")
async def rate_item(
    item_id: int,
    req: RateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedItem).where(SavedItem.id == item_id, SavedItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.user_rating = req.user_rating
    await db.commit()
    return {"id": item.id, "user_rating": item.user_rating}


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(SavedItem).where(SavedItem.id == item_id, SavedItem.user_id == user.id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.commit()
