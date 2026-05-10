import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import technicians, orders, dispatch
from database import engine, Base

# Buat tabel database jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Dispatcher System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(technicians.router, prefix="/api/technicians", tags=["Technicians"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(dispatch.router, prefix="/api/dispatch", tags=["Dispatch"])

@app.get("/")
def root():
    return {"message": "Welcome to AI Dispatcher API"}
