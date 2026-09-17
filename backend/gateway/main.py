from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gateway.routes.proxy_router import router as proxy_router
from gateway.controllers import health_controller
import httpx

app = FastAPI(
    title="API Gateway",
    description="Main entry point mapping to microservices",
    version="0.1.0",
)

# CORS Setup
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gateway Health Check
app.include_router(health_controller.router)

# Mount the Proxy Router
# All traffic going to /api/game will go to port 8002
# All traffic going to /api/auth will go to port 8001
app.include_router(proxy_router, prefix="/api")

@app.on_event("shutdown")
async def shutdown_event():
    # Close the httpx client cleanly
    from gateway.routes.proxy_router import client
    await client.aclose()

def start():
    import uvicorn
    uvicorn.run("gateway.main:app", host="0.0.0.0", port=8000, reload=True)
