from fastapi import APIRouter
from api.v1.endpoints import admins, students, schools, promoters, auth, users, add_worker, teacher, upload_documents, main_entities, reports


api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(admins.router, prefix="/admins", tags=["Admins"])
api_router.include_router(schools.router, prefix="/schools", tags=["Schools"])
api_router.include_router(promoters.router, prefix="/promoters", tags=["Promoters"])
api_router.include_router(users.router, prefix="/users", tags=["General Users"])
api_router.include_router(add_worker.router, prefix="/workers", tags=["Workers"])
api_router.include_router(teacher.router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(upload_documents.router, prefix="/documents", tags=["Worker Documents"])
api_router.include_router(main_entities.router, prefix="/main", tags=["Main Entities"])
api_router.include_router(reports.router, prefix="/reports", tags=["Student Reports"])