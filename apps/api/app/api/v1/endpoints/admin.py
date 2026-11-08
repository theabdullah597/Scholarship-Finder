from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_role
from app.models.user import User

router = APIRouter()


class AdminTestResponse(BaseModel):
    message: str
    admin_id: str


@router.get(
    "/test-rbac",
    response_model=AdminTestResponse,
    summary="RBAC verification test route (Admin only)",
)
async def test_admin_rbac(
    current_admin: User = Depends(require_role(["admin"])),
) -> AdminTestResponse:
    return AdminTestResponse(
        message="Admin privileges verified",
        admin_id=str(current_admin.id),
    )

