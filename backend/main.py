from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import db
from api.v1.endpoints import users, reviews, profile, social, interactions
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect_to_db()

    yield

    db.close_db_connection()


app = FastAPI(title="LeadrBoard", lifespan=lifespan)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(
    interactions.router, prefix="/api/v1/interactions", tags=["interactions"]
)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
