import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorGridFSBucket,
)

from app.core.config import settings
from app.core.exceptions import (
    BusinessError,
    business_error_handler,
    http_error_handler,
    validation_error_handler,
    unexpected_error_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo kết nối MongoDB
    client = AsyncIOMotorClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=3000,
    )

    app.state.mongo_client = client
    app.state.mongo_db = client[settings.MONGO_DB_NAME]
    app.state.gridfs = AsyncIOMotorGridFSBucket(
        app.state.mongo_db
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

    try:
        # 1. Ping MongoDB, tối đa 3 giây
        await asyncio.wait_for(
            db.command("ping"),
            timeout=3,
        )

        # 2. Ghi file thử vào GridFS, tối đa 5 giây
        file_id = await asyncio.wait_for(
            gridfs.upload_from_stream(
                f"health-check-{uuid4().hex}.txt",
                b"gridfs-health-check",
            ),
            timeout=5,
        )

        # 3. Đọc lại file, tối đa 5 giây
        stream = await asyncio.wait_for(
            gridfs.open_download_stream(file_id),
            timeout=5,
        )

        content = await asyncio.wait_for(
            stream.read(),
            timeout=5,
        )

        if content != b"gridfs-health-check":
            raise RuntimeError("GridFS content mismatch")

        return {
            "status": "ready",
            "database": "ok",
            "gridfs": "ok",
            "version": settings.GIT_SHA,
        }

    except Exception as exc:
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

