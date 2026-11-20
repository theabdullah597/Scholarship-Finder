from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    admin_dashboard,
    admin_opportunities,
    admin_sources,
    auth,
    health,
    opportunities,
    search,
    student,
    users,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_v1_router.include_router(opportunities.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(student.router)
api_v1_router.include_router(admin_opportunities.router)
api_v1_router.include_router(admin_dashboard.router)
api_v1_router.include_router(admin_sources.router)
