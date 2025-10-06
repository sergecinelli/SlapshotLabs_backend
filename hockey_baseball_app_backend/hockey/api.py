from django.shortcuts import get_object_or_404
from ninja import Router
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from .schemas import ObjectId, GoalieIn, GoalieOut
from .models import Goalie

router = Router(tags=["Hockey"])

@router.get('/goalies', response=list[GoalieOut])
def get_goalies(request: HttpRequest):
    goalies = Goalie.objects.all()
    return goalies

@router.get('/goalie/{goalie_id}', response=GoalieOut)
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    return goalie

@router.post('/goalie', response=ObjectId)
def add_goalie(request: HttpRequest, data: GoalieIn):
    goalie = Goalie.objects.create(**data.dict())
    return {"id": goalie.id}
