from typing import Optional
from ninja import Field, Schema

from users.utils.roles import Role, get_constant_class_int_description, get_constant_class_str_description

class UserIn(Schema):
    email: str
    first_name: str
    last_name: str
    password: str

class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: str
    country: str
    region: str
    city: str
    street: str
    postal_code: str
    role_id: int = Field(..., description=get_constant_class_int_description(Role))
    role_name: str = Field(..., description=get_constant_class_str_description(Role))
    team_id: int | None = None

    @staticmethod
    def resolve_role_id(obj) -> int:
        return obj.role

    @staticmethod
    def resolve_role_name(obj) -> str:
        return Role.get_name_by_id(obj.role)

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

class UserSearch(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserSearchOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str

class SignInSchema(Schema):
    email: str
    password: str
    remember_me: bool = False

class Message(Schema):
    message: str

class ErrorDictSchema(Schema):
    errors: str

class ResetRequestSchema(Schema):
    email: str

class ResetConfirmSchema(Schema):
    uidb64: str
    token: str
    new_password: str
    new_password_confirm: str

class CSRFTokenSchema(Schema):
    csrf_token: str
    