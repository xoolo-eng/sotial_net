from controller import Controller
from snet.web.user.views import ActivateView, TokenCreate

Controller.add("/activate/{user_code:[0-9a-f]{64}}", ActivateView, name="activate_view")
Controller.add("/token", TokenCreate, name="create_token")
