from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from models.models import CityDB, UserDB
from schemas.schemas import CityBase, CityOut

from core.auth import get_current_user
from typing import List

router = APIRouter()


@router.post("/admin/cities", response_model=CityOut)
def create_city(city: CityBase, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to create cities")
    
    if db.query(CityDB).filter(CityDB.name == city.name).first():
        raise HTTPException(status_code=400, detail="City already exists")
    
    db_city = CityDB(name=city.name)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


@router.get("/cities", response_model=List[CityOut])
def get_cities(db: Session = Depends(get_db)):
    return db.query(CityDB).all()
