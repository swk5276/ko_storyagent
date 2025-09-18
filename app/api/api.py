from fastapi import APIRouter
from app.api.endpoints import auth, users, stories, regions, matching, storybook_generation

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(storybook_generation.router, prefix="/storybook", tags=["storybook"])
