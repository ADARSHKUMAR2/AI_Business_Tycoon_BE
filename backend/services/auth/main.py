import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from services.auth.routes import auth_routes
from shared.exceptions import (
    BusinessTycoonException,
    log_business_exception,
    log_request_validation_error,
)
from shared.database import init_db
import os

logger = logging.getLogger("auth-service")

app = FastAPI(
    title="Auth Service",
    description="AI Business Tycoon Authentication Service",
    version="0.1.0",
)

async def auth_exception_handler(request: Request, exc: BusinessTycoonException):
    log_business_exception(logger, request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"message": exc.message, "details": exc.details}},
    )


async def auth_validation_exception_handler(request: Request, exc: RequestValidationError):
    await log_request_validation_error(logger, request, exc)
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"message": "Request validation failed", "details": exc.errors()}},
    )


app.add_exception_handler(BusinessTycoonException, auth_exception_handler)
app.add_exception_handler(RequestValidationError, auth_validation_exception_handler)

app.include_router(auth_routes.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Auth Service Started on Port 8001!")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auth-service"}
