from fastapi import FastAPI

from backend.routers.appointment_router import router as appointment_router

app = FastAPI(title="HMS Appointment Management", version="0.1.0")

app.include_router(appointment_router)


@app.get("/health")
def health():
    return {"status": "ok"}
