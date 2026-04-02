from fastapi import APIRouter

from .zombie import routes as zombie_routes
from .user import routes as user_routes

main_router = APIRouter(
    prefix="/api/v1",
)

main_router.include_router(user_routes.router)
main_router.include_router(zombie_routes.router)
