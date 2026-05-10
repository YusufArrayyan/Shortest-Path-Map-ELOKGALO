from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class TechnicianStatus(str, enum.Enum):
    active = "active"
    busy = "busy"
    offline = "offline"

class OrderStatus(str, enum.Enum):
    pending = "pending"
    dispatched = "dispatched"
    ongoing = "ongoing"
    done = "done"
    cancelled = "cancelled"

class Technician(Base):
    __tablename__ = "technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    skill = Column(String)
    status = Column(Enum(TechnicianStatus), default=TechnicianStatus.offline)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    locations = relationship("TechnicianLocation", back_populates="technician")
    orders = relationship("Order", back_populates="technician")

class TechnicianLocation(Base):
    __tablename__ = "technician_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    area = Column(String, nullable=True)
    
    technician = relationship("Technician", back_populates="locations")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    customer_lat = Column(Float)
    customer_lon = Column(Float)
    description = Column(String)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    technician = relationship("Technician", back_populates="orders")
