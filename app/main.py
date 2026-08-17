from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.redis import close_redis
from app.api.auth import router as auth_router
from app.api.users import router as user_router
from app.api.products import router as product_router
from app.api.orders import router as order_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)
app.include_router(product_router, prefix=settings.API_V1_STR)
app.include_router(order_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)