from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request
from services.auth.routes import auth_routes
from shared.exceptions import BusinessTycoonException
from shared.database import init_db
import os

app = FastAPI(
    title="Auth Service",
    description="AI Business Tycoon Authentication Service",
    version="0.1.0",
)

async def auth_exception_handler(request: Request, exc: BusinessTycoonException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"message": exc.message, "details": exc.details}}
    )

app.add_exception_handler(BusinessTycoonException, auth_exception_handler)

app.include_router(auth_routes.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Auth Service Started on Port 8001!")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auth-service"}
