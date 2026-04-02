from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, courses, professors

app = FastAPI(
    title="Gaucho Course Optimizer API",
    description="REST API exposing UCSB professor rankings by Gaucho Score",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
