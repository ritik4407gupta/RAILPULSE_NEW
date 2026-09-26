from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password
from app.db.mongodb import db


async def get_user(username: str) -> dict | None:
    if db.db is None:
        return None
    return await db.db["users"].find_one({"username": username})


async def create_user(
    username: str,
    password: str,
    role: str = "PASSENGER",
    full_name: str | None = None,
) -> dict:
    if db.db is None:
        raise RuntimeError("Database is not connected")

    document = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "full_name": full_name,
    }
    try:
        await db.db["users"].insert_one(document)
    except DuplicateKeyError as exc:
        raise ValueError("Username already registered") from exc
    return document


async def seed_user(username: str, password: str, role: str) -> None:
    if not username or not password or db.db is None:
        return
    if await get_user(username) is None:
        await create_user(username, password, role)


async def seed_default_users(settings) -> None:
    await seed_user(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, "ADMIN")
    await seed_user(settings.STAFF_USERNAME, settings.STAFF_PASSWORD, "STAFF")
