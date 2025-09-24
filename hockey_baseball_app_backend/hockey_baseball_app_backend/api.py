from ninja import NinjaAPI
from ninja.security import SessionAuth
from users.api import router as users_router
from hockey.api import router as hockey_router

api = NinjaAPI(csrf=True)

api.add_router("/users/", users_router)
api.add_router("/hockey/", hockey_router, auth=SessionAuth())
