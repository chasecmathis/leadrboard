from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.social import router as social_router
from app.api.games import router as game_router
from app.api.reviews import router as review_router
from app.api.interactions import router as interactions_router
from app.api.feed import router as feed_router


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic here
    yield
    # Shutdown logic here


# App Initialization
app = FastAPI(
    title="LeadrBoard API Backend",
    description="A FastAPI application to interact with LeadrBoard",
    version="1.0.0",
    lifespan=lifespan,
)

# Include Modular Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(social_router)
app.include_router(game_router)
app.include_router(review_router)
app.include_router(interactions_router)
app.include_router(feed_router)

print(f"Ruff should be mad at this!")


# Global Health Check
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "database": "connected"}


@app.get("/", tags=["System"])
async def root():
    return {"message": "Welcome to your FastAPI backend"}
