from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, async_engine
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})...")
    # Auto-initialize database tables safely
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized.")
    except Exception as e:
        logger.warning(f"Database schema auto-initialization deferred or failed: {e!s}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")
    try:
        await async_engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="LeadOS API",
    version=settings.APP_VERSION,
    description=(
        "Production-Minded, Evidence-First B2B Prospecting Platform API. "
        "Every company claim is traceable to primary sources and every lead score has an explicit explanation."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ORIGINS) if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        errors.append(
            {
                "field": loc,
                "message": err.get("msg", "Validation error"),
                "type": err.get("type", "value_error"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check the supplied query and filter parameters.",
                "details": errors,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc) or "Internal server error",
                "type": exc.__class__.__name__,
            },
        },
    )



# Mount versioned API routes
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "api_v1": "/api/v1",
        "status": "operational",
    }
