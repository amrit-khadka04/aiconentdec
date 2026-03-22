import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.detect import router
from services.ml_detector import DeepfakeDetector

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FrameScope")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print("Loading ML model...")
    app.state.detector = DeepfakeDetector()
    print("Model ready.")


app.include_router(router, prefix="/api")
