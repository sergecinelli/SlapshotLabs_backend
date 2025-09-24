from ninja import Router
from django.contrib.auth import get_user_model

router = Router()

@router.get('/goalies')
def get_goalies(request):
    return {"test": "ok"}
