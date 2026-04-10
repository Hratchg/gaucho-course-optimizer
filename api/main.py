from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, courses, professors, quarters
from api.config import settings

app = FastAPI(
    title="Gaucho Course Optimizer API",
    description="REST API exposing UCSB professor rankings by Gaucho Score",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
app.include_router(quarters.router, prefix="/quarters", tags=["quarters"])
