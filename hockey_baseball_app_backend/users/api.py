import datetime
from typing import Union
from ninja import Router
from ninja.security import SessionAuth
from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash, password_validation
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from .models import CustomUser
from .schemas import CSRFTokenSchema, Message, ErrorDictSchema, UserIn, UserEdit, UserOut, SignInSchema, ResetConfirmSchema, ResetRequestSchema, UserSearch, UserSearchOut

router = Router(tags=["Users"])

User = get_user_model()

@router.post("/csrf")
@csrf_exempt
@ensure_csrf_cookie
def get_csrf_token(request):
    """CSRF token endpoint - returns token in JSON and sets cookie"""
    csrf_token = get_token(request)
    if not csrf_token:
        # Generate new token if not available
        from django.middleware.csrf import _get_new_csrf_token
        csrf_token = _get_new_csrf_token()
    response = JsonResponse({"csrf_token": csrf_token})
    return response

@router.post('/signup', response={201: Message, 400: Message})
def create_user(request: HttpRequest, data: UserIn):
    try:
        password_validation.validate_password(data.password)
        User.objects.create_user(email=data.email, password=data.password, first_name=data.first_name, last_name=data.last_name)
    except ValidationError:
        return 400, {'message': 'Password is too simple or short.'}
    except IntegrityError:
        return 400, {'message': 'User already exists or data is incomplete.'}
    return 201, {'message': 'Created'}

@router.post('/signin', response={204: None, 403: Message})
def sign_in(request: HttpRequest, credentials: SignInSchema):
    user = authenticate(email=credentials.email, password=credentials.password)
    if user is None:
        return 403, {'message': 'Forbidden'}
    login(request, user)
    if credentials.remember_me:
        request.session.set_expiry(31622400)    # 366 days.
    return 204, None

@router.get('/signout', auth=SessionAuth(), response={204: None})
def sign_out(request: HttpRequest):
    logout(request)
    return 204, None

@router.get('/get', auth=SessionAuth(), response=UserOut)
def get_user(request: HttpRequest):
    return request.user

@router.post('/search', auth=SessionAuth(), response=list[UserSearchOut])
def search_users(request: HttpRequest, data: UserSearch):
    users = User.objects
    if data.ids is not None:
        users = users.filter(id__in=data.ids)
    if data.email is not None:
        users = users.filter(email__icontains=data.email)
    if data.first_name is not None:
        users = users.filter(first_name__icontains=data.first_name)
    if data.last_name is not None:
        users = users.filter(last_name__icontains=data.last_name)
    return users.all()

@router.patch('/edit', auth=SessionAuth(), response={204: None, 400: Message})
def edit_user(request: HttpRequest, data: UserEdit):
    user = request.user

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
        try:
            password_validation.validate_password(data.password)
        except ValidationError:
            return 400, {'message': 'Password is too simple or short.'}
        user.set_password(data.password)
        update_session_auth_hash(request, user)

    user.save()

    return 204, None

# region Password reset.

@router.post("/passwordreset/", response={200: Message, 400: ErrorDictSchema})
def request_password_reset(request: HttpRequest, data: ResetRequestSchema):
    form = PasswordResetForm(data=data.dict())
    if form.is_valid():
        form.save(
            request=request,
            use_https=request.is_secure(),
            from_email=None,  # DEFAULT_FROM_EMAIL is used.
            email_template_name='registration/password_reset_email1.html',
            subject_template_name='registration/password_reset_subject1.txt'
        )
        return {"message": "Email has been sent successfully."}
    return 400, {"errors": form.errors}

@router.post("/passwordresetconfirm/", response={200: Message, 400: Union[Message, ErrorDictSchema]})
def confirm_password_reset(request: HttpRequest, data: ResetConfirmSchema):
    try:
        uid = urlsafe_base64_decode(data.uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return 400, {"message": "Invalid user"}

    if not default_token_generator.check_token(user, data.token):
        return 400, {"message": "Invalid or expired token"}

    form = SetPasswordForm(user, data={
        'new_password1': data.new_password,
        'new_password2': data.new_password_confirm,
    })
    if form.is_valid():
        form.save()
        return {"message": "Password has been reset successfully."}
    return 400, {"errors": str(form.errors.as_text())}

# endregion
