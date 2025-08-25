
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, kids, schedule, rewards, activities
from .settings import settings
from app.models.base import Base, engine
from app.scripts.seed import seed_demo

app = FastAPI(title="Homeschool Helper API")

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed_demo()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(kids.router, prefix="/kids", tags=["kids"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(rewards.router, prefix="/rewards", tags=["rewards"])
app.include_router(activities.router, prefix="/activities", tags=["activities"])

@app.get("/")
def root():
    return {"status": "ok"}
