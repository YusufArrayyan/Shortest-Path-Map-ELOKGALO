import sys
import os

# Tambahkan backend/ ke path agar import relatif berfungsi
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import technicians, orders, dispatch, route
from database import engine, Base

# Buat tabel database jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Dispatcher System", version="1.0.0")

# CORS — izinkan GitHub Pages dan localhost untuk development
ALLOWED_ORIGINS = [
    "https://yusufarrayyan.github.io",
    "https://yusufarrayyan.github.io/",
    "https://yusufarray.github.io",
    "https://yusufarray.github.io/",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(technicians.router, prefix="/api/technicians", tags=["Technicians"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(dispatch.router, prefix="/api/dispatch", tags=["Dispatch"])
app.include_router(route.router, prefix="/api/route", tags=["Route"])

@app.get("/")
def root():
    return {"message": "AI Dispatcher API is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}
