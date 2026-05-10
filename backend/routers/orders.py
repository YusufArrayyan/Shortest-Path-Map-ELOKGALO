from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore
from pydantic import BaseModel # type: ignore
from database import get_db # type: ignore
import models # type: ignore

router = APIRouter()

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_lat: float
    customer_lon: float
    description: str

@router.post("/")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(  # type: ignore
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_lat=order.customer_lat,
        customer_lon=order.customer_lon,
        description=order.description
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return {
        "status": "success",
        "message": "Order berhasil dibuat",
        "data": {
            "order_id": db_order.id,
            "status": db_order.status,
            "created_at": db_order.created_at
        }
    }
