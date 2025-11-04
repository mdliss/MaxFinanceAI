from fastapi import APIRouter
from app.api import users, consent, signals, personas, recommendations, guardrails, operator, evaluation, profiles

api_router = APIRouter()

api_router.include_router(users.router)
api_router.include_router(consent.router)
api_router.include_router(signals.router)
api_router.include_router(personas.router)
api_router.include_router(recommendations.router)
api_router.include_router(guardrails.router)
api_router.include_router(operator.router)
api_router.include_router(evaluation.router)
api_router.include_router(profiles.router)

__all__ = ["api_router"]
