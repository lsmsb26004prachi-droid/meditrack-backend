from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """What the app sends to create an account."""

    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["patient", "doctor"] = "patient"


class UserLogin(BaseModel):
    """What the app sends to log in."""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """What the backend sends back about a user. It never includes the password."""

    id: int
    full_name: str
    email: EmailStr
    role: Literal["patient", "doctor"]
    
    # New Profile Fields
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None


class Token(BaseModel):
    """The login token the app keeps and sends with later requests."""

    access_token: str
    token_type: str = "bearer"


class UserProfileUpdate(BaseModel):
    """What the app sends to update the user's physical profile."""
    
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None