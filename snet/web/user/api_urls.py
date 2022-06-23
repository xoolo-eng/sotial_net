from controller import Controller
from snet.web.user.views import UserView, TokenView


Controller.add("", UserView, name="user_endpoint")
Controller.add("/token", TokenView, name="token_endpoint")
