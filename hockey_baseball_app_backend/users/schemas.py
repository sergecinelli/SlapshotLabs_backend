from typing import Optional
from ninja import Schema

class UserIn(Schema):
    email: str
    first_name: str
    last_name: str
    password: str

class UserOut(Schema):
    email: str
    first_name: str
    last_name: str
    phone_number: str
    country: str
    region: str
    city: str
    street: str
    postal_code: str

class UserEdit(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    password: Optional[str] = None

class SignInSchema(Schema):
    email: str
    password: str

class Message(Schema):
    message: str
