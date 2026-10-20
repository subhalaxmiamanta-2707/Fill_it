from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    id_token: str

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: str
    vehicle_number: Optional[str] = None
    vehicle_chassis: Optional[str] = None

class UserModel(BaseModel):
    name: str
    email: EmailStr
    role: str
    phone: Optional[str] = None



