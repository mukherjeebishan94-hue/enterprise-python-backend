from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limiter import limiter
from app.api.auth import router as auth_router

app = FastAPI(title="Python Backend API")

# Add Rate Limiter State & Exception Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])