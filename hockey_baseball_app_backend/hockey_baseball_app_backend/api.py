import datetime
from ninja import NinjaAPI
from ninja.renderers import JSONRenderer, NinjaJSONEncoder
from ninja.security import SessionAuth
from users.api import router as users_router
from hockey.api import router as hockey_router

class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, v):
        if isinstance(v, datetime.timedelta):
            return f"{(int(v.total_seconds() // 60)):02d}:{(int(v.total_seconds() % 60)):02d}"
        return super().default(v)

class CustomJsonRenderer(JSONRenderer):
    encoder_class = CustomJsonEncoder

api = NinjaAPI(csrf=True, renderer=CustomJsonRenderer())

api.add_router("/users/", users_router)
api.add_router("/hockey/", hockey_router, auth=SessionAuth())
