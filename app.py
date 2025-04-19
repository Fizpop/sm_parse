from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
from backend.api.media_routes import router as media_router
from backend.models.database import Base, engine

# Створюємо необхідні директорії
UPLOAD_DIR = Path("uploads")
DB_DIR = Path("db")
for dir_path in [UPLOAD_DIR, DB_DIR]:
    dir_path.mkdir(exist_ok=True)

app = FastAPI(title="UA Media Scanner",
             description="Система пошуку та аналізу нових українських ЗМІ",
             version="1.0.0")

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL фронтенду
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтуємо статичні файли
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Створюємо таблиці
Base.metadata.create_all(bind=engine)

# Підключаємо роутери
app.include_router(media_router, prefix="/api/v1", tags=["media"])

@app.get("/")
async def root():
    return {"message": "UA Media Scanner API"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 