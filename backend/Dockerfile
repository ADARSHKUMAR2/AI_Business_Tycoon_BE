FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install uv without adding development dependencies to the runtime image.
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

# Install the locked production dependencies before copying application code
# to make dependency installation reusable by Docker's build cache.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY gateway ./gateway
COPY services ./services
COPY shared ./shared

# Default to the public API gateway. Cloud Run deployments of the auth and
# game services override this command to select their respective FastAPI app.
CMD ["uv", "run", "--no-sync", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]