from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.system.router import router as system_router
from app.modules.users.presentation.router import router as users_router

router = APIRouter()
router.include_router(system_router)
router.include_router(auth_router)
router.include_router(users_router)
