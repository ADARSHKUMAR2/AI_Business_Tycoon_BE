from fastapi import FastAPI

app = FastAPI(
    title="Auth Service",
    description="AI Business Tycoon Authentication Service",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auth-service"}

# Placeholder for Phase 2 Auth endpoints
@app.post("/login")
async def login():
    return {"message": "Auth service is running (Phase 1 Stub)"}
