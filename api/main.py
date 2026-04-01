from fastapi import FastAPI
from api.routers import health, courses, professors

app = FastAPI(
    title="Gaucho Course Optimizer API",
    description="REST API exposing UCSB professor rankings by Gaucho Score",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
