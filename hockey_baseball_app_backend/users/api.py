from ninja import Router
from ninja.security import SessionAuth
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login, logout
from .models import CustomUser
from .schemas import Message, UserIn, UserEdit, UserOut, SignInSchema

router = Router()

@router.post('/signup', response={201: Message})
def create_user(request, data: UserIn):
    User = get_user_model()
    User.objects.create_user(email=data.email, password=data.password, first_name=data.first_name, last_name=data.last_name)
    return 201, {'message': 'Created'}

@router.post('/signin', response={204: None, 403: Message})
def sign_in(request, credentials: SignInSchema):
    user = authenticate(email=credentials.email, password=credentials.password)
    if user is None:
        return 403, {'message': 'Forbidden'}
    login(request, user)
    return 204, None

@router.get('/signout', auth=SessionAuth(), response={204: None})
def sign_out(request):
    logout(request)
    return 204, None

@router.get('/get', auth=SessionAuth(), response=UserOut)
def get_user(request):
    return request.user

@router.post('/edit', auth=SessionAuth(), response={204: None})
def edit_user(request, data: UserEdit):
    user: CustomUser = request.user

    if data.email is not None:
        user.email = data.email
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.country is not None:
        user.country = data.country
    if data.region is not None:
        user.region = data.region
    if data.city is not None:
        user.city = data.city
    if data.street is not None:
        user.street = data.street
    if data.postal_code is not None:
        user.postal_code = data.postal_code
    if data.password is not None:
        user.set_password(data.password)

    user.save()

    return 204, None
