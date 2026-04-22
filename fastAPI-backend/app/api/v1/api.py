from fastapi import APIRouter
from app.api.v1.endpoints import admins, students, schools, promoters, auth, users, donors, hopes, posts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(admins.router, prefix="/admins", tags=["Admins"])
api_router.include_router(schools.router, prefix="/schools", tags=["Schools"])
api_router.include_router(promoters.router, prefix="/promoters", tags=["Promoters"])
api_router.include_router(users.router, prefix="/users", tags=["General Users"])
api_router.include_router(donors.router, prefix="/donors", tags=["Donors"])
api_router.include_router(hopes.router, prefix="/hopes", tags=["Hopes / Donations"])
api_router.include_router(posts.router, prefix="/posts", tags=["Social Feed"])