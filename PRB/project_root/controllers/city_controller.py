from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from models.models import CityDB
from schemas.schemas import CityBase, CityOut
from typing import List

router = APIRouter(prefix="/cities", tags=["Cities"])

# این روت به admin_controller.py منتقل شد
# @router.post("/admin/cities", response_model=CityOut)
# def create_city(city: CityBase, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
#     # ...

@router.get("/", response_model=List[CityOut])
def get_cities(db: Session = Depends(get_db)):
    """
    دریافت لیست تمامی شهرها.
    """
    return db.query(CityDB).all()