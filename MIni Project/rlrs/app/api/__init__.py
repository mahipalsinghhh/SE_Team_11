from fastapi import APIRouter

from app.api import attendance, audit, health, reminders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(reminders.router)
api_router.include_router(attendance.router)
api_router.include_router(audit.router)
