import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from dotenv import load_dotenv

from routes.database import engine, Base, async_session, User, get_db
from auth import validate_init_data
from routes.promotion import router as promotion_router
from routes.promotion import Promotion

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(promotion_router)
app.include_router(Promotion.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow()}


@app.post("/api/auth")
async def auth(request: Request):

    body = await request.json()

    init_data = body.get("initData")

    if not init_data:
        raise HTTPException(400, "Missing initData")

    user = validate_init_data(init_data, BOT_TOKEN)

    if user["id"] not in ADMIN_IDS:
        raise HTTPException(403, "Not admin")

    return {
        "ok": True,
        "user": user,
        "is_admin": True
    }


@app.get("/api/stats")
async def stats(db: AsyncSession = Depends(get_db)):

    total = await db.scalar(select(func.count()).select_from(User))

    consented = await db.scalar(
        select(func.count()).where(User.consented == True)
    )

    pending = await db.scalar(
        select(func.count()).where(User.consented == False)
    )

    return {
        "total_users": total or 0,
        "consented": consented or 0,
        "pending": pending or 0
    }


@app.get("/api/users")
async def users(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User))

    users = result.scalars().all()

    return [
        {
            "id": u.telegram_id,
            "username": u.username,
            "first_name": u.first_name,
            "consented": u.consented,
            "banned": u.banned
        }
        for u in users
    ]


@app.post("/api/ban")
async def ban(data: dict, db: AsyncSession = Depends(get_db)):

    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(400, "Missing user_id")

    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(404, "User not found")

    user.banned = True

    await db.commit()

    return {"ok": True}