from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.algorithm_service import AlgorithmService

router = APIRouter()

class RouteRequest(BaseModel):
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float
    algorithm: str = "astar"

@router.post("/")
def calculate_route(req: RouteRequest):
    """
    Hitung rute terpendek antara dua titik koordinat.
    Digunakan untuk fitur UNIB Campus Navigator.
    """
    if req.algorithm == "astar":
        result = AlgorithmService.astar(
            req.from_lat, req.from_lon,
            req.to_lat, req.to_lon
        )
    elif req.algorithm == "dijkstra":
        result = AlgorithmService.dijkstra(
            req.from_lat, req.from_lon,
            req.to_lat, req.to_lon
        )
    else:
        raise HTTPException(status_code=400, detail="Algoritma tidak valid. Gunakan 'astar' atau 'dijkstra'.")

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Rute tidak ditemukan"))

    return {
        "status": "success",
        "algorithm": result["algorithm"],
        "distance_meters": result["distance_meters"],
        "duration_seconds": result["duration_seconds"],
        "eta_minutes": round(result["duration_seconds"] / 60, 1),
        "polyline": result["polyline"]
    }
