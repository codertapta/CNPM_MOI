import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorGridFSBucket,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.pois import router as pois_router
from app.core.config import settings
from app.core.exceptions import (
    BusinessError,
    business_error_handler,
    http_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo kết nối MongoDB
    client = AsyncIOMotorClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=3000,
    )

    app.state.mongo_client = client
    app.state.mongo_db = client[settings.MONGO_DB_NAME]
    app.state.gridfs = AsyncIOMotorGridFSBucket(app.state.mongo_db)
    # Tao index dia ly de truy van POI gan vi tri nguoi dung
    await app.state.mongo_db["pois"].create_index(
        [("location", "2dsphere")],
        name="pois_location_2dsphere",
    )

    try:
        yield
    finally:
        # Đóng kết nối khi ứng dụng dừng
        client.close()


# Khởi tạo FastAPI
app = FastAPI(
    title="AutomaticDubbing API",
    lifespan=lifespan,
)
app.include_router(pois_router)
APP_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = APP_ROOT / "frontend" / "dist"

if not FRONTEND_DIST.is_dir():
    FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIST / "assets"),
    name="assets",
)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIST / "assets"),
    name="static",
)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)


# Đăng ký các exception handler
app.add_exception_handler(
    BusinessError,
    business_error_handler,
)

app.add_exception_handler(
    StarletteHTTPException,
    http_error_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,
)

app.add_exception_handler(
    Exception,
    unexpected_error_handler,
)


# Kiểm tra ứng dụng còn hoạt động
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.GIT_SHA,
    }


# Kiểm tra MongoDB và GridFS có hoạt động


@app.get("/health/ready")
async def health_ready(request: Request):
    db = request.app.state.mongo_db
    gridfs = request.app.state.gridfs
    file_id = None
    logger.info("Readiness check: starting MongoDB ping")

    try:
        # 1. Ping MongoDB, tối đa 3 giây
        await asyncio.wait_for(
            db.command("ping"),
            timeout=3,
        )
        logger.info("Readiness check: MongoDB ping succeeded")

        # 2. Ghi file thử vào GridFS, tối đa 5 giây
        file_id = await asyncio.wait_for(
            gridfs.upload_from_stream(
                f"health-check-{uuid4().hex}.txt",
                b"gridfs-health-check",
            ),
            timeout=5,
        )
        logger.info("Readiness check: GridFS upload succeeded")

        # 3. Đọc lại file, tối đa 5 giây
        stream = await asyncio.wait_for(
            gridfs.open_download_stream(file_id),
            timeout=5,
        )
        logger.info("Readiness check: GridFS download stream opened")

        content = await asyncio.wait_for(
            stream.read(),
            timeout=5,
        )
        logger.info("Readiness check: GridFS read succeeded")

        if content != b"gridfs-health-check":
            raise RuntimeError("GridFS content mismatch")

        return {
            "status": "ready",
            "database": "ok",
            "gridfs": "ok",
            "version": settings.GIT_SHA,
        }

    except Exception as exc:
        logger.exception("MongoDB/GridFS readiness check failed")
        raise HTTPException(
            status_code=503,
            detail="Service not ready: MongoDB or GridFS check failed",
        ) from exc

    finally:
        if file_id is not None:
            try:
                await asyncio.wait_for(
                    gridfs.delete(file_id),
                    timeout=3,
                )
            except Exception:
                pass


@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_fallback(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(
            status_code=404,
            detail="API endpoint not found",
        )

    index_file = FRONTEND_DIST / "index.html"

    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend build not found",
        )

    return FileResponse(index_file)
