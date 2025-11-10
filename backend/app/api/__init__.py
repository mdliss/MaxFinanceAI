from fastapi import APIRouter
from app.api import users, consent, signals, personas, recommendations, guardrails, operator, evaluation, profiles, accounts, transactions, chat, goals, budgets, alerts, admin

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
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(chat.router)
# V2 Endpoints
api_router.include_router(goals.router)
api_router.include_router(budgets.router)
api_router.include_router(alerts.router)
# Admin Endpoints
api_router.include_router(admin.router)

__all__ = ["api_router"]
