from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from services.dispatch_service import DispatchService
import models

router = APIRouter()

class DispatchRequest(BaseModel):
    order_id: int
    algorithm: str = "astar"

@router.post("/")
def dispatch_order(req: DispatchRequest, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == req.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    technicians_db = db.query(models.Technician).filter(models.Technician.status == "active").all()
    
    tech_list = []
    for t in technicians_db:
        loc = db.query(models.TechnicianLocation).filter(
            models.TechnicianLocation.technician_id == t.id
        ).order_by(models.TechnicianLocation.recorded_at.desc()).first()
        
        if loc:
            tech_list.append({
                "id": t.id,
                "name": t.name,
                "location": {"latitude": loc.latitude, "longitude": loc.longitude}
            })

    if not tech_list:
        raise HTTPException(status_code=400, detail="Tidak ada teknisi aktif")

    result = DispatchService.dispatch_all(
        tech_list,
        order.customer_lat,
        order.customer_lon,
        req.algorithm
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    best = result["selected"]
    
    # Update order
    order.technician_id = best["id"]
    order.status = "dispatched"
    db.commit()

    return {
        "status": "success",
        "order_id": req.order_id,
        "selected_technician": {
            "id": best["id"],
            "name": best["name"],
            "distance_meters": best["route"]["distance_meters"],
            "duration_seconds": best["route"]["duration_seconds"],
            "eta_minutes": round(best["route"]["duration_seconds"] / 60, 1)
        },
        "all_routes": [
            {
                "technician_id": r["id"],
                "name": r["name"],
                "distance_meters": r["route"]["distance_meters"],
                "duration_seconds": r["route"]["duration_seconds"],
                "is_selected": r["id"] == best["id"]
            }
            for r in result["all_routes"]
        ],
        "polyline": best["route"]["polyline"]
    }
