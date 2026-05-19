from fastapi import FastAPI

from lpi.routers import goals, recommendations, signals

app = FastAPI(
    title="LPI Platform",
    description="Life Programmable Interface: goal registry, activity signals, recommendation engine",
    version="0.1.0",
)

app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
