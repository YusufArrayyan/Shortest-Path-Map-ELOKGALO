from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore
from database import get_db # type: ignore
import models # type: ignore

router = APIRouter()

@router.get("/active")
def get_active_technicians(db: Session = Depends(get_db)):
    technicians = db.query(models.Technician).filter(models.Technician.status == "active").all()
    
    result = []
    for t in technicians:
        # Ambil lokasi terakhir
        loc = db.query(models.TechnicianLocation).filter(
            models.TechnicianLocation.technician_id == t.id
        ).order_by(models.TechnicianLocation.recorded_at.desc()).first()
        
        if loc:
            result.append({
                "id": t.id,
                "name": t.name,
                "skill": t.skill,
                "status": t.status,
                "rating": t.rating,
                "location": {
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "area": loc.area
                }
            })
            
    return {"status": "success", "count": len(result), "data": result}

@router.post("/dummy")
def create_dummy_data(db: Session = Depends(get_db)):
    # Buat data dummy untuk testing
    techs = [
        models.Technician(name="Budi Santoso", skill="AC", status="active"), # type: ignore
        models.Technician(name="Andi Pratama", skill="Listrik", status="active"), # type: ignore
        models.Technician(name="Reza Hidayat", skill="Elektronik", status="active") # type: ignore
    ]
    db.add_all(techs)
    db.commit()
    
    locs = [
        models.TechnicianLocation(technician_id=1, latitude=-3.7714, longitude=102.2595, area="Rawa Makmur"), # type: ignore
        models.TechnicianLocation(technician_id=2, latitude=-3.8671, longitude=102.2703, area="Pantai Panjang"), # type: ignore
        models.TechnicianLocation(technician_id=3, latitude=-3.7932, longitude=102.3105, area="Lingkar Timur") # type: ignore
    ]
    db.add_all(locs)
    db.commit()
    
    return {"message": "Dummy data created"}
