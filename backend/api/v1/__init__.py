"""
API v1 Router aggregation.
"""
from fastapi import APIRouter
from backend.api.v1.dashboard import router as dashboard_router
from backend.api.v1.transactions import router as transactions_router
from backend.api.v1.actions import router as actions_router
from backend.api.v1.simulator import router as simulator_router
from backend.api.v1.ml import router as ml_router

api_router = APIRouter()
api_router.include_router(dashboard_router)
api_router.include_router(transactions_router)
api_router.include_router(actions_router)
api_router.include_router(simulator_router)
api_router.include_router(ml_router)
