from controller import Controller
from snet.web.chat import views


Controller.add("/{chat_id:[0-9a-f]{16}}", views.ChatView, name="chat_endpoint")
Controller.add("", views.ChatPageView, name="chat_page_endpoint")
